No funciona el pluging claude code en dev container: no comparte la autenticación con claude code fuera dev container.

Lo siguiente es la información de diagnóstico de /status y de `claude doctor`
----
System Diagnostics
   ⚠ installMethod is native, but claude command not found at /home/vscode/.local/bin/claude
   ⚠ Insufficient permissions for auto-updates
   ⚠ No write permissions for auto-updates (requires sudo)

Diagnostics
 └ Currently running: npm-global (2.1.14)
 └ Path: /usr/bin/node
 └ Invoked: /usr/bin/claude
 └ Config install method: native
 └ Search: OK (vendor)
 Warning: Insufficient permissions for auto-updates
 Fix: Do one of: (1) Re-install node without sudo, or (2) Use `claude install` for native installation

 Updates
 └ Auto-updates: enabled
 └ Update permissions: No (requires sudo)
 └ Auto-update channel: latest
 └ Stable version: 2.1.5
 └ Latest version: 2.1.14

 Version Locks
 └ No active version locks
----

Lo siguiente es la información de `claude doctor` fuera de dev container:
----
Diagnostics
 └ Currently running: native (2.1.14)
 └ Path: /Users/jose/.local/share/claude/versions/2.1.14
 └ Invoked: /Users/jose/.local/share/claude/versions/2.1.14
 └ Config install method: native
 └ Search: OK (bundled)

 Updates
 └ Auto-updates: enabled
 └ Auto-update channel: latest
 └ Stable version: 2.1.5
 └ Latest version: 2.1.14

 Version Locks
 └ No active version locks
----

Revisa la configuración de dev container para que:
- node use claude code instalado fuera de dev container
- claude code dentro de dev container comparta toda la configuración fuera de dev containner incluida la información de autenticación. Revisa la configuración actual dado que puede no ser correcta
- 