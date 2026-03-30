# Commands and Workflow

Use this reference for the top-level `dft-cp2k` router workflow.

## Router role

`dft-cp2k` does not own full task templates. It dispatches to one subskill path:

- `dft-cp2k/static`
- `dft-cp2k/relax`
- `dft-cp2k/md`
- `dft-cp2k/electronic`

## Dispatch checklist

1. Identify task intent from user request.
1. Verify minimal prerequisites (structure, basis/potential set, restart context if needed).
1. Route to one subskill.
1. Let subskill generate task-specific CP2K input layout.
1. If execution is requested, hand off to `dpdisp-submit`.

## Intent to subskill mapping

- single-point SCF/energy -> `dft-cp2k/static`
- geometry optimization -> `dft-cp2k/relax`
- molecular dynamics -> `dft-cp2k/md`
- electronic analysis -> `dft-cp2k/electronic`

## Shared output contract

All subskills should return:

1. task directory/file set
1. parameter summary
1. explicit assumptions and unresolved choices
1. submission handoff note when requested
