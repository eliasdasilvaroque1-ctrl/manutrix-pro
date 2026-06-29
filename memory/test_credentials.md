# MAINTRIX Test Credentials

## Master Account
- Email: master@manutrix.com
- Password: master123
- Role: master
- Visibility: ALL data

## Test Users (Aditivo 002 - Visibility Testing)

### Admin
- Email: test.admin@maintrix.com
- Password: admin123
- Role: admin
- Visibility: All records of the organization

### PCM
- Email: test.pcm@maintrix.com
- Password: pcm123
- Role: pcm
- Visibility: All disciplines of the organization

### Supervisor Mecânico
- Email: test.sup.mec@maintrix.com
- Password: sup123
- Role: supervisor
- Disciplina Principal: mecanica
- Áreas: PLANTA-01, PLANTA-02
- Turno: A
- Visibility: Only mecanica OS/inspections in PLANTA-01 and PLANTA-02

### Supervisor Elétrico
- Email: test.sup.ele@maintrix.com
- Password: sup123
- Role: supervisor
- Disciplina Principal: eletrica
- Disciplinas Secundárias: instrumentacao
- Áreas: PLANTA-02, PLANTA-03
- Turno: A
- Visibility: Only eletrica+instrumentacao OS/inspections in PLANTA-02 and PLANTA-03

### Mecânico (Técnico)
- Email: test.mec@maintrix.com
- Password: tec123
- Role: tecnico
- Disciplina Principal: mecanica
- Áreas: PLANTA-01, PLANTA-02
- Turno: A
- Visibility: Only mecanica OS in PLANTA-01 and PLANTA-02

### Eletricista (Técnico)
- Email: test.ele@maintrix.com
- Password: tec123
- Role: tecnico
- Disciplina Principal: eletrica
- Disciplinas Secundárias: instrumentacao
- Áreas: PLANTA-02, PLANTA-03
- Turno: B
- Visibility: Only eletrica+instrumentacao OS in PLANTA-02 and PLANTA-03

### Operador
- Email: test.operador@maintrix.com
- Password: op123
- Role: operador
- Disciplina Principal: producao
- Áreas: PLANTA-01
- Turno: A
- Visibility: Only producao+civil OS. NEVER sees mecanica/eletrica/instrumentacao

## Existing Users (Legacy)
- admin@manutrix.com / admin123 (admin)
- supervisor@manutrix.com / supervisor123 (supervisor)
- tecnico@manutrix.com / tecnico123 (tecnico)
- pcm@manutrix.com / pcm123 (pcm)
