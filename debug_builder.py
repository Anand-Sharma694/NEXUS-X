import sys
sys.path.insert(0, '/Users/sharm/Desktop/NEXUS-X/NEXUS-X_PRODUCT_V3_POSTGRESQL')
from backend.project_builder import UniversalProjectBuilder

result = UniversalProjectBuilder.build('Launch payments and security in 10 days with a team of 3 people.')
print("Tasks:")
for t in result['tasks'][:5]:
    print(f"  {t['task_key']}: {t['name']}")
print("\nDependencies:")
for dep in result['dependencies'][:10]:
    print(f"  {dep[0]} -> {dep[1]}")
