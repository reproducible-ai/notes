#!/usr/bin/env python3
"""Calculate a recipe-specific cost estimate from compact, retained measurements.

This is a calculator, not a model-artifact verifier. Input evidence and rate
assumptions must be reviewed before its output is published in notes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

METHOD = "steady-throughput-plus-fixed/v1"


def number(value, label, *, positive=False):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
        or (positive and value == 0)
    ):
        raise ValueError(
            f"{label} must be a finite {'positive' if positive else 'nonnegative'} number"
        )
    return value


def integer(value, label, *, positive=False):
    number(value, label, positive=positive)
    if not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def periodic_cost(schedule, full_steps, label):
    every = schedule["everySteps"]
    if every is not None:
        integer(every, f"{label}.everySteps", positive=True)
    if not isinstance(schedule["atEnd"], bool):
        raise ValueError(f"{label}.atEnd must be boolean")
    count = full_steps // every if every else 0
    if schedule["atEnd"] and (every is None or full_steps % every):
        count += 1
    seconds = schedule["secondsPerOperation"]
    if count:
        number(seconds, f"{label}.secondsPerOperation", positive=True)
    elif seconds is not None:
        number(seconds, f"{label}.secondsPerOperation")
    return count, count * (seconds or 0)


def estimate(data):
    if data["schema"] != "reproai.cost-input/v1":
        raise ValueError("unsupported cost input schema")
    for key in ("model", "scope", "hardware", "evidence", "limitations"):
        if not data[key]:
            raise ValueError(f"missing {key}")
    full_steps = integer(data["fullSteps"], "fullSteps", positive=True)
    points = data["points"]
    if not points or len({p["id"] for p in points}) != len(points):
        raise ValueError("measurements need unique point IDs")
    rates, startups = [], []
    for point in points:
        if point["outcome"] != "completed" or point["exitCode"] != 0:
            raise ValueError("all declared points must have completed successfully")
        steps = integer(point["completedSteps"], "completedSteps", positive=True)
        updates = integer(point["steadyUpdates"], "steadyUpdates", positive=True)
        seconds = number(point["steadySeconds"], "steadySeconds", positive=True)
        duration = number(point["trainingProcessSeconds"], "trainingProcessSeconds", positive=True)
        if point["requestedSteps"] != steps or not 50 <= updates <= steps <= full_steps:
            raise ValueError("point counts disagree or contain fewer than 50 steady updates")
        if seconds > duration:
            raise ValueError("steady timing exceeds the training process")
        rate = seconds / updates
        startup = duration - steps * rate
        number(startup, "training startup residual")
        rates.append(rate)
        startups.append(startup)
    spread = (max(rates) - min(rates)) / min(rates)
    if spread > 0.2:
        raise ValueError(
            "steady rates differ by more than 20%; collect representative measurements"
        )
    seconds_per_update = math.fsum(p["steadySeconds"] for p in points) / sum(
        p["steadyUpdates"] for p in points
    )
    checkpoint_count, checkpoint_seconds = periodic_cost(
        data["checkpoint"], full_steps, "checkpoint"
    )
    evaluation_count, evaluation_seconds = periodic_cost(
        data["evaluation"], full_steps, "evaluation"
    )
    components = {
        "setupSeconds": number(data["setupSeconds"], "setupSeconds"),
        "trainingStartupSeconds": mean(startups),
        "trainingUpdateSeconds": full_steps * seconds_per_update,
        "checkpointSeconds": checkpoint_seconds,
        "evaluationSeconds": evaluation_seconds,
        "finalizationSeconds": number(data["finalizationSeconds"], "finalizationSeconds"),
    }
    rate = data["rate"]
    if rate["unit"] != "allocation" or not rate["source"] or not rate["observedAt"]:
        raise ValueError("a dated, sourced rate for the whole allocation is required")
    hourly = number(rate["usdPerHour"], "usdPerHour", positive=True)
    increment = integer(rate["billingIncrementSeconds"], "billingIncrementSeconds", positive=True)
    minimum = integer(rate["minimumBilledSeconds"], "minimumBilledSeconds")
    other = number(data["otherCostUsd"], "otherCostUsd")
    duration = math.fsum(components.values())
    billed = math.ceil(max(duration, minimum) / increment) * increment
    compute = billed * hourly / 3600
    return {
        "schema": "reproai.cost-estimate/v1",
        "method": METHOD,
        "model": data["model"],
        "scope": data["scope"],
        "fullSteps": full_steps,
        "hardware": data["hardware"],
        "confidence": "low",
        "secondsPerUpdate": seconds_per_update,
        "pointSecondsPerUpdate": rates,
        "pointStartupSeconds": startups,
        "steadyRateSpread": spread,
        "extrapolationFactor": full_steps / max(p["completedSteps"] for p in points),
        "checkpointCount": checkpoint_count,
        "evaluationCount": evaluation_count,
        "components": components,
        "durationSeconds": duration,
        "billedSeconds": billed,
        "rate": rate,
        "computeCostUsd": compute,
        "otherCostUsd": other,
        "calculatedCostUsd": compute + other,
        "estimateUsd": math.ceil(compute + other),
        "rounding": "rounded up to whole USD; forecast precision is not cent-level",
        "limitations": data["limitations"],
        "evidence": data["evidence"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    try:
        result = estimate(json.loads(raw))
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        parser.exit(2, f"Cannot estimate: {exc}\n")
    result["inputSha256"] = hashlib.sha256(raw).hexdigest()
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
