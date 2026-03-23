# Commands and Workflow

Use this reference for the top-level `dft-vasp` router workflow.

## Router role

`dft-vasp` does not own full task templates. It dispatches to one subskill path:

- `dft-vasp/static`
- `dft-vasp/relax`
- `dft-vasp/dos`
- `dft-vasp/band`

## Dispatch checklist

1. Identify task intent from user request.
1. Verify minimal prerequisites.
1. Route to one subskill.
1. Let subskill generate task-specific files.
1. If execution is requested, hand off to `dpdisp-submit`.

## Intent to subskill mapping

- single-point SCF/energy -> `dft-vasp/static`
- geometry optimization -> `dft-vasp/relax`
- density of states -> `dft-vasp/dos`
- band structure -> `dft-vasp/band`

## Shared output contract

All subskills should return:

1. task directory/file set
1. parameter summary
1. explicit assumptions and unresolved choices
1. submission handoff note when requested
