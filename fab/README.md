# Fabrication Outputs

Use this folder for generated manufacturing artifacts, organized per project:

- `fab/<project>/gerber/`
- `fab/<project>/drill/`
- `fab/<project>/position/`
- `fab/<project>/bom/`

Guidelines:

- Keep generated outputs separate from source KiCad files.
- Regenerate outputs from current source before release/manufacturing.
- Include a short note per release with generation date, source project path, and tool versions.
