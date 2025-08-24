# 🔒 Security Guidelines

This document outlines security best practices for the ChatBot project.

## 🚨 Critical Security Rules

### ❌ NEVER COMMIT:
- API keys, tokens, or passwords
- Database files (*.db, *.sqlite)
- Log files (*.log)
- Large model files (*.bin, *.model, etc.)
- Environment files with real secrets (.env)
- SSH keys or certificates

### ✅ ALWAYS:
- Use .env.example templates
- Keep real .env files in .gitignore
- Use config.json.example for configuration templates
- Store large models outside git (Docker volumes, Git LFS, etc.)
- Run security checks regularly

## 📁 File Structure Security

### Environment Files
```
✅ .env.example          # Template - safe to commit
❌ .env                  # Real secrets - NEVER commit
✅ frontend/.env.example # Template - safe to commit  
❌ frontend/.env         # Real config - NEVER commit
```

### Configuration Files
```
✅ backend/config.json.example  # Template - safe to commit
❌ backend/config.json          # Real config - NEVER commit
```

### Data Files
```
❌ backend/data/         # Database and user data
❌ backend/logs/         # Application logs
❌ backend_vosk_vi/      # Large model files
❌ *.db, *.sqlite        # Database files
```

## 🛠️ Security Tools

### Automated Security Check
Run the security check script:
```bash
./scripts/security_check.sh
```

This script checks for:
- Tracked sensitive files
- API keys in code
- Large files
- Database files
- Log files
- .gitignore effectiveness

### Manual Checks
```bash
# Check for tracked .env files
git ls-files | grep "\.env$"

# Check for large files (>1MB)
git ls-files | xargs ls -la 2>/dev/null | awk '$5 > 1048576'

# Check for potential secrets in tracked files
git ls-files | xargs grep -i -E "api[_-]?key|secret|token|password"
```

## 🔧 Setup Instructions

### 1. Environment Setup
```bash
# Copy templates
cp .env.example .env
cp frontend/.env.example frontend/.env
cp backend/config.json.example backend/config.json

# Edit with your real values
nano .env
nano backend/config.json
```

### 2. Verify .gitignore
Ensure these patterns are in .gitignore:
```
# Environment files
.env
*.env
!*.env.example

# Configuration files
backend/config.json
config/secrets.json

# Data and logs
*.db
*.sqlite*
*.log
backend/data/
backend/logs/

# Large files
*.bin
*.model
*.zip
backend_vosk_vi/
```

### 3. Clean Existing Repository
If you've accidentally committed sensitive files:
```bash
# Remove from git history (DANGEROUS - backup first!)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env backend/config.json' \
  --prune-empty --tag-name-filter cat -- --all

# Force push (WARNING: This rewrites history)
git push origin --force --all
```

## 🚀 Docker Security

### Environment Variables
Use Docker secrets or environment variables:
```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - API_KEY=${API_KEY}
    env_file:
      - .env
```

### Volume Security
```yaml
volumes:
  # Use named volumes for sensitive data
  vosk_models:
  db_data:
```

## 📊 Security Checklist

### Before Each Commit
- [ ] Run `./scripts/security_check.sh`
- [ ] Check `git status` for sensitive files
- [ ] Verify no API keys in diff: `git diff --cached`
- [ ] Ensure .env files are ignored

### Regular Maintenance
- [ ] Update .gitignore patterns
- [ ] Rotate API keys periodically
- [ ] Review access logs
- [ ] Update dependencies for security patches

### Production Deployment
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/TLS
- [ ] Set up proper authentication
- [ ] Configure rate limiting
- [ ] Monitor for security issues

## 🆘 Security Incident Response

### If Secrets Are Committed:
1. **Immediately** rotate all exposed credentials
2. Remove from git history (see cleanup commands above)
3. Force push to overwrite history
4. Notify team members to re-clone repository
5. Review access logs for potential misuse

### If Large Files Are Committed:
1. Remove files from git: `git rm --cached <file>`
2. Add to .gitignore
3. Use Git LFS for future large files
4. Consider repository cleanup if history is bloated

## 📞 Security Contacts

- **Security Issues**: Create a private issue or contact maintainers
- **Vulnerability Reports**: Follow responsible disclosure practices
- **Emergency**: Immediately rotate credentials and notify team

## 🔗 Additional Resources

- [Git Security Best Practices](https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work)
- [Docker Security](https://docs.docker.com/engine/security/)
- [Environment Variables Security](https://12factor.net/config)
- [API Key Management](https://owasp.org/www-project-api-security/)

---

**Remember**: Security is everyone's responsibility. When in doubt, ask for review before committing!