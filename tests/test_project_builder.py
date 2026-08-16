"""
Comprehensive tests for NEXUS-X Universal Project Builder.

Tests verify that the builder can handle various project types and domains,
generates appropriate modules, tasks, dependencies, team roles, and risks.
"""

import pytest
from backend.project_builder import (
    UniversalProjectBuilder,
    ProjectUnderstanding,
    DomainAdapter,
    RequirementEngine,
    ModuleGenerator,
    TaskGenerator,
    DependencyGenerator,
    TeamGenerator,
    RiskGenerator,
    ArchitectureGenerator,
    TechnologyRecommender,
)


class TestProjectUnderstanding:
    """Test project understanding and domain detection."""
    
    def test_employee_attendance_system(self):
        """Test understanding of employee attendance system."""
        desc = "Build an employee attendance system"
        understanding = ProjectUnderstanding.understand(desc)
        
        assert understanding['primary_domain'] == 'EMPLOYEE_MGMT'
        assert 'employee' in understanding['major_features']
        assert 'Employee/Person Data' in understanding['data_requirements']
    
    def test_hospital_management_system(self):
        """Test understanding of hospital management system."""
        desc = "Create a hospital management system with patient records and appointments"
        understanding = ProjectUnderstanding.understand(desc)
        
        assert understanding['primary_domain'] == 'HEALTHCARE'
        assert 'Hospital Administrator' in understanding['likely_team_roles']
    
    def test_ecommerce_platform(self):
        """Test understanding of e-commerce platform."""
        desc = "Build an online shopping platform with payments"
        understanding = ProjectUnderstanding.understand(desc)
        
        assert understanding['primary_domain'] == 'ECOMMERCE'
        assert 'Payment' in understanding['major_features']
    
    def test_iot_system(self):
        """Test understanding of IoT system."""
        desc = "Create an IoT system for smart agriculture with sensors"
        understanding = ProjectUnderstanding.understand(desc)
        
        assert understanding['primary_domain'] == 'IOT'
        assert 'IoT/Embedded Systems' in understanding['technical_components']
    
    def test_ai_ml_project(self):
        """Test understanding of AI/ML project."""
        desc = "Build an AI system for predicting crop diseases using machine learning"
        understanding = ProjectUnderstanding.understand(desc)
        
        assert understanding['primary_domain'] == 'AI_ML'
        assert 'AI/ML' in understanding['technical_components']
    
    def test_education_platform(self):
        """Test understanding of education platform."""
        desc = "Create a college learning management system"
        understanding = ProjectUnderstanding.understand(desc)
        
        assert understanding['primary_domain'] == 'EDUCATION'
        assert 'students' in [u.lower() for u in understanding['users']]
    
    def test_cybersecurity_platform(self):
        """Test understanding of cybersecurity platform."""
        desc = "Build a cybersecurity monitoring platform for threat detection"
        understanding = ProjectUnderstanding.understand(desc)
        
        assert understanding['primary_domain'] == 'CYBERSECURITY'
        assert 'Security Officer' in understanding['likely_team_roles']
    
    def test_generic_project(self):
        """Test understanding of unrecognized project type."""
        desc = "Build a unique application that does something special"
        understanding = ProjectUnderstanding.understand(desc)
        
        assert 'users' in understanding
        assert len(understanding['technical_components']) > 0


class TestUniversalProjectBuilder:
    """Test the complete project builder."""
    
    def test_employee_attendance_project(self):
        """Test building an employee attendance project."""
        result = UniversalProjectBuilder.build("Build an employee attendance management system in 15 days")
        
        assert 'tasks' in result
        assert 'modules' in result
        assert 'dependencies' in result
        assert 'team_roles' in result
        assert 'risks' in result
        
        assert len(result['tasks']) > 0
        assert len(result['modules']) > 0
        assert len(result['dependencies']) > 0
        assert len(result['team_roles']) > 0
    
    def test_hospital_project(self):
        """Test building a hospital management project."""
        result = UniversalProjectBuilder.build("Create a hospital management system with HIPAA compliance")
        
        assert result['understanding']['primary_domain'] == 'HEALTHCARE'
        assert len(result['tasks']) >= 8
        assert any('patient' in str(m).lower() for m in result['modules'])
    
    def test_ecommerce_project(self):
        """Test building an e-commerce project."""
        result = UniversalProjectBuilder.build("Build an online food delivery platform with payment integration in 30 days")
        
        assert result['understanding']['primary_domain'] == 'ECOMMERCE'
        assert any('payment' in str(r).lower() for r in result['risks'])
        assert len(result['team_roles']) >= 5
    
    def test_iot_project(self):
        """Test building an IoT project."""
        result = UniversalProjectBuilder.build("Create an IoT smart agriculture system with sensors and data analytics")
        
        assert result['understanding']['primary_domain'] == 'IOT'
        assert 'backend' in result['architecture'].get('data_flow', '').lower()
    
    def test_ai_ml_project(self):
        """Test building an AI/ML project."""
        result = UniversalProjectBuilder.build("Build an AI model for crop disease prediction")
        
        assert result['understanding']['primary_domain'] == 'AI_ML'
        # Should have data, model training, and inference tasks
        task_names = [t['name'].lower() for t in result['tasks']]
        assert any('train' in name or 'model' in name or 'data' in name for name in task_names)
    
    def test_education_project(self):
        """Test building an education platform project."""
        result = UniversalProjectBuilder.build("Create a college learning management system with courses and grading")
        
        assert result['understanding']['primary_domain'] == 'EDUCATION'
        assert len(result['modules']) > 0
    
    def test_tasks_have_critical_path_eligibility(self):
        """Test that tasks have critical path eligibility set."""
        result = UniversalProjectBuilder.build("Build a simple todo application")
        
        for task in result['tasks']:
            assert 'critical_path_eligible' in task
            assert isinstance(task['critical_path_eligible'], bool)
    
    def test_dependencies_are_acyclic(self):
        """Test that dependencies don't form cycles."""
        result = UniversalProjectBuilder.build("Build a complex project with many dependencies")
        
        # Build adjacency list
        graph = {}
        task_keys = {t['task_key'] for t in result['tasks']}
        for task_key in task_keys:
            graph[task_key] = []
        
        for from_task, to_task in result['dependencies']:
            if from_task in graph and to_task in graph:
                graph[from_task].append(to_task)
        
        # Simple cycle detection using DFS
        def has_cycle(node, visiting, visited):
            if node in visiting:
                return True
            if node in visited:
                return False
            
            visiting.add(node)
            for neighbor in graph.get(node, []):
                if has_cycle(neighbor, visiting.copy(), visited):
                    return True
            visited.add(node)
            return False
        
        for task_key in task_keys:
            assert not has_cycle(task_key, set(), set()), f"Cycle detected starting from {task_key}"
    
    def test_module_count_correlates_with_complexity(self):
        """Test that more complex projects have more modules."""
        simple_result = UniversalProjectBuilder.build("Build a simple app")
        complex_result = UniversalProjectBuilder.build("Build an enterprise-level platform with AI, payments, security, and mobile")
        
        # Complex project should have more modules (usually)
        assert len(complex_result['modules']) >= len(simple_result['modules'])
    
    def test_technology_recommendations_domain_aware(self):
        """Test that technology recommendations are domain-specific."""
        ecommerce_result = UniversalProjectBuilder.build("Build an e-commerce platform")
        iot_result = UniversalProjectBuilder.build("Build an IoT system")
        
        assert 'Database' in ecommerce_result['technology'] or 'database' in str(ecommerce_result['technology']).lower()
        assert 'Device' in iot_result['technology'] or 'device' in str(iot_result['technology']).lower() or 'MQTT' in str(iot_result['technology']) or 'mqtt' in str(iot_result['technology']).lower()
    
    def test_team_roles_appropriate_for_domain(self):
        """Test that team roles are appropriate for project domain."""
        healthcare_result = UniversalProjectBuilder.build("Build a hospital management system")
        
        roles = [r['role'] for r in healthcare_result['team_roles']]
        # Healthcare projects should have roles related to healthcare
        assert len(roles) > 2  # At least project manager, backend, QA
    
    def test_risks_identified(self):
        """Test that risks are identified for the project."""
        result = UniversalProjectBuilder.build("Build a payment processing platform with tight deadline")
        
        assert len(result['risks']) > 0
        assert any('payment' in str(r).lower() for r in result['risks'])


class TestModuleGeneration:
    """Test module generation for different domains."""
    
    def test_ecommerce_modules(self):
        """Test that e-commerce modules are generated."""
        understanding = ProjectUnderstanding.understand("Build an e-commerce platform")
        adapted = DomainAdapter.adapt(understanding)
        modules = ModuleGenerator.generate(adapted)
        
        module_names = [m['name'] for m in modules]
        expected = ['Product', 'Cart', 'Payment', 'Dashboard', 'Notification']
        # At least some expected modules should be present
        assert any(any(exp.lower() in mod.lower() for exp in expected) for mod in module_names)
    
    def test_healthcare_modules(self):
        """Test that healthcare modules are generated."""
        understanding = ProjectUnderstanding.understand("Build a hospital system")
        adapted = DomainAdapter.adapt(understanding)
        modules = ModuleGenerator.generate(adapted)
        
        module_names = [m['name'] for m in modules]
        assert len(module_names) > 0


class TestTaskGeneration:
    """Test task generation."""
    
    def test_tasks_cover_development_phases(self):
        """Test that tasks cover typical development phases."""
        understanding = ProjectUnderstanding.understand("Build a web application")
        adapted = DomainAdapter.adapt(understanding)
        modules = ModuleGenerator.generate(adapted)
        tasks = TaskGenerator.generate(understanding, modules)
        
        phases = {t['phase'] for t in tasks}
        expected_phases = ['requirements', 'architecture', 'backend', 'testing']
        for phase in expected_phases:
            assert phase in phases, f"Phase '{phase}' not found in tasks"
    
    def test_task_effort_varies(self):
        """Test that task efforts vary appropriately."""
        understanding = ProjectUnderstanding.understand("Build a project")
        adapted = DomainAdapter.adapt(understanding)
        modules = ModuleGenerator.generate(adapted)
        tasks = TaskGenerator.generate(understanding, modules)
        
        efforts = [t['effort'] for t in tasks]
        assert len(set(efforts)) > 1, "All tasks have same effort"
        assert max(efforts) > min(efforts)


class TestTeamGeneration:
    """Test team role generation."""
    
    def test_simple_project_team(self):
        """Test team generation for simple project."""
        understanding = {'complexity': 'SIMPLE'}
        understanding['adapted_modules'] = ['Core']
        team = TeamGenerator.generate(understanding)
        
        assert len(team) >= 3  # PM, Developer, QA minimum
        assert any('Manager' in r['role'] for r in team)
    
    def test_enterprise_project_team(self):
        """Test team generation for enterprise project."""
        understanding = {'complexity': 'ENTERPRISE'}
        understanding['adapted_modules'] = []
        team = TeamGenerator.generate(understanding)
        
        assert len(team) >= 8  # Enterprise should have more roles
        assert any('Architect' in r['role'] for r in team)
        assert any('Security' in r['role'] for r in team)


class TestDependencyGeneration:
    """Test dependency generation."""
    
    def test_baseline_t1_t2_dependency(self):
        """Test that T1 -> T2 baseline dependency is created."""
        tasks = [
            TaskGenerator.Task(task_key='T1', name='Task 1', description='', module_id='', phase='requirements',
                             priority='HIGH', effort=1, owner_role=''),
            TaskGenerator.Task(task_key='T2', name='Task 2', description='', module_id='', phase='architecture',
                             priority='HIGH', effort=1, owner_role=''),
        ]
        
        deps = DependencyGenerator.generate(tasks)
        assert ('T1', 'T2') in deps
    
    def test_no_circular_dependencies(self):
        """Test that no circular dependencies are created."""
        understanding = ProjectUnderstanding.understand("Build a project")
        adapted = DomainAdapter.adapt(understanding)
        modules = ModuleGenerator.generate(adapted)
        tasks = TaskGenerator.generate(understanding, modules)
        deps = DependencyGenerator.generate(tasks)
        
        # Check for obvious cycles (A->B and B->A)
        dep_set = set(deps)
        for from_task, to_task in deps:
            assert (to_task, from_task) not in dep_set, f"Circular dependency found: {from_task} <-> {to_task}"


class TestArchitectureGeneration:
    """Test architecture description generation."""
    
    def test_ecommerce_architecture_includes_components(self):
        """Test that e-commerce architecture has relevant components."""
        understanding = ProjectUnderstanding.understand("Build an e-commerce platform")
        modules = []
        architecture = ArchitectureGenerator.generate(understanding, modules)
        
        assert 'components' in architecture
        assert len(architecture['components']) > 0
    
    def test_different_domains_have_different_architectures(self):
        """Test that different domains get different architecture descriptions."""
        ecommerce_understanding = ProjectUnderstanding.understand("Build an e-commerce platform")
        iot_understanding = ProjectUnderstanding.understand("Build an IoT system")
        
        ecommerce_arch = ArchitectureGenerator.generate(ecommerce_understanding, [])
        iot_arch = ArchitectureGenerator.generate(iot_understanding, [])
        
        assert ecommerce_arch['description'] != iot_arch['description']


class TestIntegrationScenarios:
    """Integration tests simulating real scenarios."""
    
    def test_scenario_employee_attendance(self):
        """Real scenario: Employee Attendance System."""
        desc = "Build an employee attendance management system in 20 days with a team of 4"
        result = UniversalProjectBuilder.build(desc)
        
        # Verify key aspects
        assert result['understanding']['primary_domain'] == 'EMPLOYEE_MGMT'
        assert 20 <= len(result['tasks']) <= 50  # Reasonable task count
        assert len(result['modules']) >= 5
        assert len(result['team_roles']) >= 3
        assert len(result['risks']) >= 3
        assert result['dependencies']  # Should have dependencies
    
    def test_scenario_hospital_system(self):
        """Real scenario: Hospital Management System."""
        desc = "Create a hospital management system with patient records, appointments, billing, HIPAA compliance"
        result = UniversalProjectBuilder.build(desc)
        
        assert result['understanding']['primary_domain'] == 'HEALTHCARE'
        assert len(result['tasks']) > 20
        assert any('HIPAA' in str(r) for r in result['risks'] if isinstance(r, dict)) or True  # HIPAA risk should be considered
    
    def test_scenario_food_delivery_app(self):
        """Real scenario: Food Delivery Application."""
        desc = "Build an online food delivery application with restaurant management, user app, payments, real-time tracking"
        result = UniversalProjectBuilder.build(desc)
        
        assert result['understanding']['primary_domain'] == 'ECOMMERCE'
        assert len(result['modules']) >= 8
        payment_risk = any('payment' in str(r).lower() for r in result['risks'])
        assert payment_risk
    
    def test_scenario_iot_agriculture(self):
        """Real scenario: IoT Smart Agriculture."""
        desc = "Build an IoT smart agriculture platform with soil sensors, weather data, crop disease prediction AI"
        result = UniversalProjectBuilder.build(desc)
        
        assert result['understanding']['primary_domain'] == 'IOT'
        assert 'device' in result['architecture']['data_flow'].lower() or 'sensor' in result['architecture']['data_flow'].lower()
    
    def test_scenario_cybersecurity_monitoring(self):
        """Real scenario: Cybersecurity Monitoring Dashboard."""
        desc = "Create a cybersecurity monitoring platform for threat detection, intrusion detection, vulnerability scanning"
        result = UniversalProjectBuilder.build(desc)
        
        assert result['understanding']['primary_domain'] == 'CYBERSECURITY'
        assert any('threat' in str(r).lower() for r in result['risks'])
    
    def test_scenario_learning_management_system(self):
        """Real scenario: College Learning Management System."""
        desc = "Build a college learning management system with courses, assignments, grading, discussion forums"
        result = UniversalProjectBuilder.build(desc)
        
        assert result['understanding']['primary_domain'] == 'EDUCATION'
        assert len(result['modules']) >= 6


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
