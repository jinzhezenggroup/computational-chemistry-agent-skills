# Commands and Workflow

Use this reference for the top-level `dftbplus` router workflow.

## Router role

`dftbplus` does not own full task templates. It dispatches to one subskill path:

- `dftbplus/static`
- `dftbplus/relax`
- `dftbplus/md`
- `dftbplus/electronic`

## Dispatch checklist

1. Identify task intent from user request.
1. Verify minimal prerequisites (structure, parameter set, restart context if needed).
1. Route to one subskill.
1. Let subskill generate task-specific input/script layout.
1. If execution is requested, hand off to `dpdisp-submit`.

## Intent to subskill mapping

- single-point SCF/energy -> `dftbplus/static`
- geometry optimization -> `dftbplus/relax`
- molecular dynamics -> `dftbplus/md`
- electronic analysis (band/DOS-like) -> `dftbplus/electronic`

## Shared output contract

All subskills should return:

1. task directory/file set
1. parameter summary
1. explicit assumptions and unresolved choices
1. submission handoff note when requested
