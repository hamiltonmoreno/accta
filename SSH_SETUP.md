# Configuracao de Chave SSH para Deploy via GitHub Actions

## Guia Passo a Passo

---

### Passo 1 — Gerar o par de chaves SSH (no seu computador local)

Abra o terminal e execute:

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/accta_deploy
```

Quando pedir passphrase, deixe **vazio** (pressione Enter duas vezes).

Isto cria dois ficheiros:

| Ficheiro | Tipo | Finalidade |
|----------|------|------------|
| `~/.ssh/accta_deploy` | Chave **privada** | Vai para o GitHub Secrets |
| `~/.ssh/accta_deploy.pub` | Chave **publica** | Vai para o servidor |

---

### Passo 2 — Adicionar a chave publica ao servidor

Conecte-se ao servidor de producao:

```bash
ssh root@SEU_IP_DO_SERVIDOR
```

Depois adicione a chave publica:

```bash
# Criar diretorio se nao existir
mkdir -p ~/.ssh && chmod 700 ~/.ssh

# Adicionar a chave publica (SUBSTITUA pelo conteudo real)
echo "COLE_AQUI_O_CONTEUDO_DE_accta_deploy.pub" >> ~/.ssh/authorized_keys

# Definir permissoes corretas
chmod 600 ~/.ssh/authorized_keys
```

**Para obter o conteudo da chave publica** (no seu computador local):

```bash
cat ~/.ssh/accta_deploy.pub
```

Exemplo de output (copie TUDO, incluindo `ssh-ed25519`):

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJ... github-actions-deploy
```

---

### Passo 3 — Testar a conexao SSH (no seu computador local)

```bash
ssh -i ~/.ssh/accta_deploy root@SEU_IP_DO_SERVIDOR "echo 'Conexao OK!'"
```

Se aparecer `Conexao OK!`, a chave esta configurada corretamente.

---

### Passo 4 — Adicionar a chave privada como GitHub Secret

**4.1** Copie o conteudo COMPLETO da chave privada:

```bash
cat ~/.ssh/accta_deploy
```

O output sera algo como:

```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACCJ... (varias linhas)
-----END OPENSSH PRIVATE KEY-----
```

**Copie TUDO**, incluindo as linhas `-----BEGIN...` e `-----END...`.

**4.2** No GitHub, aceda a:

```
Repository → Settings → Secrets and variables → Actions → New repository secret
```

**4.3** Adicione todos os secrets necessarios:

| Nome do Secret | Valor |
|----------------|-------|
| `DEPLOY_SSH_KEY` | Conteudo completo de `~/.ssh/accta_deploy` (chave privada) |
| `DEPLOY_HOST` | IP do servidor (ex: `203.0.113.50`) |
| `DEPLOY_USER` | Utilizador SSH (ex: `root` ou `deploy`) |
| `DEPLOY_PORT` | Porta SSH (ex: `22`) — opcional |
| `DEPLOY_APP_DIR` | Diretorio da app (ex: `/app`) — opcional |
| `PRODUCTION_URL` | URL publica (ex: `https://controlador.cv`) |

---

### Passo 5 — Verificar que tudo funciona

Faca um push para a branch `main`:

```bash
git add .
git commit -m "ci: setup deployment pipeline"
git push origin main
```

Depois aceda a **Repository → Actions** e verifique se o workflow `CD — Deploy to Production` executa com sucesso.

---

## Resumo Visual

```
SEU COMPUTADOR                    GITHUB                      SERVIDOR
                                                              
~/.ssh/accta_deploy      →   Secret: DEPLOY_SSH_KEY           
(chave privada)                                               
                                                              
~/.ssh/accta_deploy.pub  ─────────────────────────→  ~/.ssh/authorized_keys
(chave publica)                                      (chave publica)
                                                              
                              GitHub Actions                  
                              usa a chave privada   ────→  Autentica com
                              do Secret                    a chave publica
```

---

## Seguranca

- **NUNCA** partilhe a chave privada (`accta_deploy`) com ninguem
- **NUNCA** faca commit da chave privada no repositorio
- Se comprometida, remova a chave publica do servidor e gere um novo par
- Considere usar um utilizador dedicado `deploy` em vez de `root`

### Criar utilizador dedicado (opcional mas recomendado)

No servidor:

```bash
# Criar utilizador
adduser deploy --disabled-password

# Dar permissao de supervisor
echo "deploy ALL=(ALL) NOPASSWD: /usr/bin/supervisorctl" >> /etc/sudoers.d/deploy

# Adicionar chave SSH
mkdir -p /home/deploy/.ssh
echo "COLE_A_CHAVE_PUBLICA_AQUI" >> /home/deploy/.ssh/authorized_keys
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh

# Dar permissao na pasta da app
chown -R deploy:deploy /app
```

Depois no GitHub, use `DEPLOY_USER = deploy`.
