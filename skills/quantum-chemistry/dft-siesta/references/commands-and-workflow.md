# Commands and Workflow

Use this reference for the top-level `dft-siesta` router workflow.

## Router role

`dft-siesta` does not own full task templates. It dispatches to one subskill path:

- `dft-siesta/static`
- `dft-siesta/relax`
- `dft-siesta/md`
- `dft-siesta/electronic`

## Dispatch checklist

1. Identify task intent from user request.
1. Verify minimal prerequisites (structure, pseudopotentials, restart context if needed).
1. Route to one subskill.
1. Let subskill generate task-specific SIESTA input layout.
1. If execution is requested, hand off to `dpdisp-submit`.

## Intent to subskill mapping

- single-point SCF/energy -> `dft-siesta/static`
- geometry optimization -> `dft-siesta/relax`
- molecular dynamics -> `dft-siesta/md`
- electronic analysis -> `dft-siesta/electronic`

## Shared output contract

All subskills should return:

1. task directory/file set
1. parameter summary
1. explicit assumptions and unresolved choices
1. submission handoff note when requested
