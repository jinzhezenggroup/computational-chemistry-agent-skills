# Commands and Workflow

Use this reference for the top-level `dft-abinit` router workflow.

## Router role

`dft-abinit` does not own full task templates. It dispatches to one subskill path:

- `dft-abinit/static`
- `dft-abinit/relax`
- `dft-abinit/md`
- `dft-abinit/electronic`

## Dispatch checklist

1. Identify task intent from user request.
1. Verify minimal prerequisites (structure, pseudopotentials, restart context if needed).
1. Route to one subskill.
1. Let subskill generate task-specific ABINIT input layout.
1. If execution is requested, hand off to `dpdisp-submit`.

## Intent to subskill mapping

- single-point SCF/energy -> `dft-abinit/static`
- geometry optimization -> `dft-abinit/relax`
- molecular dynamics -> `dft-abinit/md`
- electronic analysis -> `dft-abinit/electronic`

## Shared output contract

All subskills should return:

1. task directory/file set
1. parameter summary
1. explicit assumptions and unresolved choices
1. submission handoff note when requested
