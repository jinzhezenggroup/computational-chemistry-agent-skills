# Commands and Workflow

Use this reference for the top-level `dft-gpaw` router workflow.

## Router role

`dft-gpaw` does not own full task templates. It dispatches to one subskill path:

- `dft-gpaw/static`
- `dft-gpaw/relax`
- `dft-gpaw/dos`
- `dft-gpaw/band`

## Dispatch checklist

1. Identify task intent from user request.
1. Verify minimal prerequisites.
1. Route to one subskill.
1. Let subskill generate task-specific script/input layout.
1. If execution is requested, hand off to `dpdisp-submit`.

## Intent to subskill mapping

- single-point SCF/energy -> `dft-gpaw/static`
- geometry optimization -> `dft-gpaw/relax`
- density of states -> `dft-gpaw/dos`
- band structure -> `dft-gpaw/band`

## Shared output contract

All subskills should return:

1. task directory/file set
1. parameter summary
1. explicit assumptions and unresolved choices
1. submission handoff note when requested
