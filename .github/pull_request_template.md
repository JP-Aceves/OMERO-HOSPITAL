cat > .github/pull_request_template.md <<'EOF'
## Tarea
OME-XX · Closes #N

## Qué cambia
- 

## Cómo probarlo
1. 

## Capturas (si cambia la interfaz)

## Checklist
- [ ] Sale de `develop` y va a `develop`
- [ ] Se ejecuta sin errores y `pytest` pasa
- [ ] Respeta la separación MVC y solo toca mis archivos
- [ ] Commits con formato `OME-XX: descripción`
- [ ] Tarjeta movida a "En revisión" en Notion y GitHub Projects
EOF
git add .github/pull_request_template.md
git commit -m "OME-20: adapta la plantilla de PR a Notion y GitHub Projects"