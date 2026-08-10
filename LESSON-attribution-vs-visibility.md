# Lesson: a public lineage is not an attributed one

_Reproducible AI campaign · written 2026-08-10 · reproduced from scratch, no GPU_

This is the mistake that cost the campaign a row. It is easy to make, it produces no error, and
every quality gate you are likely to run will still pass. If you are publishing lineage, read this
before your first real run.

## The short version

**Visibility and attribution are two different settings, and getting the first one right does not
give you the second.** A lineage can be fully public, fully readable, complete in every technical
respect — and still be owned by nobody. When that happens, the graph carrying your work and the
graph carrying your *name* are two different graphs, and nothing tells you.

## What it looks like when it goes wrong

You get **two DAGs from one run**:

| | attributed twin | content twin |
|---|---|---|
| jobs | **0** | **3** |
| owner | your org | **nil UUID** `00000000-…` |
| git commit | identical | identical |
| created | 02:32:05Z | 02:31:27Z |

Same commit, 38 seconds apart. The jobs went into an anonymous session; a later attributed call
created a second, **empty** one. The work is public and the attribution is public — they are just
not in the same place.

The trap is that **each half looks fine on its own.** The content twin has all the jobs and a
complete package freeze. The attributed twin has your org and your labels. Only when you ask "does
the graph I am about to cite actually contain anything?" does it fall apart.

## The cause, reproduced

`roar scope` decides where a repo publishes. Three settings, one surprise:

| `roar scope` | resulting session owner | attributed? |
|---|---|---|
| unset | nil UUID | **no** |
| `public` | nil UUID | **no** |
| a **project** scope | your organization | **yes** |

**Only a project scope attributes.** Setting scope to `public` gets you public visibility and an
anonymous owner — which is a perfectly reasonable thing for the tool to offer, and exactly the wrong
thing if you believed you were publishing under your name.

This was reproduced end to end on a throwaway repo with a two-line Python script and no GPU: four
`roar run` steps, three registrations, three different scope settings. The whole experiment costs
nothing, which is worth knowing — **you can test your publishing setup before you spend anything on
training.**

## How to not get bitten

**1. Set a project scope before your first run, not after.**

```sh
roar scope list          # shows every scope you can publish to
roar scope use "<org>/<project>"
roar scope status        # confirm: "active: project <uuid>"
```

**2. After publishing, verify the graph you intend to cite has content *and* an owner.**

The check is two fields. Do it before you build anything on top of that hash:

```python
g = load_dag(api_base, dag_hash)
jobs  = len(g.get("jobs") or [])
owner = (g["session"].get("scope") or {}).get("owner_name")
assert jobs > 0, "attributed graph is EMPTY — the content is in another session"
assert owner,    "session is ANONYMOUS — public, but owned by nobody"
```

Across ten campaign rows this check passes on nine and fails on exactly the broken one. It is cheap,
it is mechanical, and it runs **before** you spend money rather than after.

**3. Do not trust a success message. Verify the effect.**

The repair command for this situation (`republish-lineage`) reports success and does nothing. It
operates on a hash: the content lives under a hash your identity does not own, and the attributed
hash has nothing to republish. It cannot move jobs between owners, so it succeeds having changed
nothing. **A tool telling you it worked is not evidence that it worked.**

## The general principle

Reproducibility work has a recurring failure shape: **the thing that looks like the record and the
thing that is the record drift apart, silently.** A gate that reads the recording will not catch it,
because the recording is fine — it is just not the one you are pointing at.

So the habit worth building is: *after every publish, fetch the artifact you are about to cite and
assert something about its contents.* Not the command's exit code. Not the summary line. The thing
itself.

## Also worth knowing

- **`roar scope list` currently labels the `public` scope "public attributed", but it produces an
  anonymous owner.** If you read that table and chose `public` expecting attribution, you were
  reading it correctly and the label is wrong. Filed as a defect.
- **A freshly created project may not be usable as a scope immediately** — the accessible-scope list
  is carried in your auth token, so a project created after you logged in can return *"Project scope
  not available in GLaaS auth access context"* until you re-authenticate. If you hit that, do not
  fall back to `public` to get moving. That fallback is the entire bug.
