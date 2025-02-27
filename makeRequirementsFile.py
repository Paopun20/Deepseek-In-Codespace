import subprocess

# Capture the output of `pip freeze`
result = subprocess.run(["pip", "freeze"], capture_output=True, text=True)

# Extract package names (remove versions)
packages = [line.split('==')[0] for line in result.stdout.splitlines()]

# Write the unpinned packages to requirements.txt
with open('requirements.txt', 'w') as f:
    f.write('\n'.join(packages))