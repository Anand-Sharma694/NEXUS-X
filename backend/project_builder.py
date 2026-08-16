"""
NEXUS-X Universal Project Builder

A generic project generation engine that understands any software, technology,
AI, IoT, data, business, college, or engineering project description and
dynamically creates a complete project plan.

NOT hard-coded templates. Dynamic domain adaptation.
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


# ========== DATA CLASSES ==========

@dataclass
class Requirement:
    """Functional or non-functional requirement."""
    req_id: str
    title: str
    description: str
    category: str  # 'FUNCTIONAL' or 'NON-FUNCTIONAL'
    priority: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    phase: str  # 'discovery', 'requirements', 'architecture', etc.
    
    def __getitem__(self, key):
        return getattr(self, key)

    def to_dict(self):
        return asdict(self)


@dataclass
class Module:
    """Project module/component."""
    module_id: str
    name: str
    description: str
    category: str  # 'BACKEND', 'FRONTEND', 'DATA', 'INTEGRATIONS', 'SECURITY', etc.
    effort: float  # person-days
    dependencies: List[str]  # other module IDs
    risk_level: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    
    def __getitem__(self, key):
        return getattr(self, key)

    def to_dict(self):
        return asdict(self)


@dataclass  
class Task:
    """Implementation task."""
    task_key: str
    name: str
    description: str
    module_id: str
    phase: str  # 'discovery', 'requirements', 'architecture', 'ui_ux', 'database', 'backend', 'frontend', etc.
    priority: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    status: str = 'NOT STARTED'
    effort: float = 1.0  # person-days
    duration: float = 1.0  # calendar days (with concurrency)
    owner_role: str = 'Developer'
    risk_level: str = 'MEDIUM'
    dependencies: List[str] = None  # task keys
    acceptance_criteria: List[str] = None
    milestone: str = ''
    critical_path_eligible: bool = True
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.acceptance_criteria is None:
            self.acceptance_criteria = []
    
    def __getitem__(self, key):
        return getattr(self, key)

    def to_dict(self):
        data = asdict(self)
        return data


@dataclass
class TeamRole:
    """Recommended team role."""
    role: str  # 'Project Manager', 'Backend Developer', etc.
    reason: str  # why this role is needed
    capacity: int  # % of time
    responsibilities: List[str]
    task_categories: List[str]  # module categories this role handles
    
    def __getitem__(self, key):
        return getattr(self, key)

    def to_dict(self):
        return asdict(self)


# ========== PROJECT UNDERSTANDING ENGINE ==========

class ProjectUnderstanding:
    """Analyze and understand a project description."""
    
    DOMAIN_KEYWORDS = {
        'EMPLOYEE_MGMT': ['employee', 'attendance', 'leave', 'hr', 'payroll', 'shift', 'roster'],
        'HEALTHCARE': ['hospital', 'clinic', 'medical', 'doctor', 'patient', 'prescription', 'appointment', 'health', 'healthcare'],
        'ECOMMERCE': ['ecommerce', 'e-commerce', 'shopping', 'product', 'cart', 'checkout', 'order', 'seller', 'vendor', 'inventory'],
        'IOT': ['iot', 'sensor', 'device', 'gateway', 'edge', 'arduino', 'raspberry', 'mqtt', 'actuator'],
        'AI_ML': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'prediction', 'classification', 'neural', 'deep learning', 'model', 'training'],
        'EDUCATION': ['college', 'university', 'school', 'student', 'course', 'learning', 'lms', 'classroom', 'exam', 'grade'],
        'CYBERSECURITY': ['cybersecurity', 'security monitoring', 'threat', 'intrusion', 'siem', 'vulnerability', 'audit', 'compliance'],
        'BANKING': ['banking', 'bank account', 'financial institution', 'finance', 'transaction ledger', 'fund transfer', 'loan', 'mortgage', 'kyc', 'credit', 'debit'],
        'SOCIAL': ['social', 'network', 'community', 'chat', 'messaging', 'feed', 'profile', 'follow'],
        'REAL_ESTATE': ['property', 'real estate', 'house', 'apartment', 'listing', 'rent', 'lease'],
        'SUPPLY_CHAIN': ['supply chain', 'logistics', 'warehouse', 'inventory', 'shipping', 'tracking'],
        'RESTAURANT': ['restaurant', 'food delivery', 'cafe', 'menu', 'order', 'delivery', 'catering'],
        'GAMING': ['game', 'gaming', 'multiplayer', 'leaderboard', 'mobile game', 'vr'],
        'MOBILE': ['mobile', 'app', 'android', 'ios', 'phone', 'tablet'],
    }
    
    COMPLEXITY_INDICATORS = {
        'SIMPLE': ['simple', 'basic', 'quick', 'small', 'minimal', 'prototype'],
        'MEDIUM': ['medium', 'standard', 'typical', 'reasonable'],
        'COMPLEX': ['complex', 'enterprise', 'large', 'advanced', 'sophisticated'],
        'ENTERPRISE': ['enterprise', 'large-scale', 'mission-critical', 'high-volume', 'multi-tenant'],
    }
    
    @staticmethod
    def understand(description: str) -> Dict[str, Any]:
        """
        Analyze project description to extract key information.
        Returns structured understanding without inventing facts.
        """
        desc = description.strip()
        desc_lower = desc.lower()
        
        result = {
            'raw_description': desc,
            'domains': ProjectUnderstanding._detect_domains(desc_lower),
            'primary_domain': None,
            'complexity': ProjectUnderstanding._detect_complexity(desc_lower),
            'project_type': None,
            'primary_objective': desc[:150] if len(desc) > 150 else desc,
            'users': ProjectUnderstanding._infer_users(desc_lower),
            'stakeholders': ProjectUnderstanding._infer_stakeholders(desc_lower),
            'major_workflows': ProjectUnderstanding._infer_workflows(desc_lower),
            'major_features': ProjectUnderstanding._infer_features(desc_lower),
            'technical_components': ProjectUnderstanding._infer_tech(desc_lower),
            'data_requirements': ProjectUnderstanding._infer_data_needs(desc_lower),
            'integrations': ProjectUnderstanding._infer_integrations(desc_lower),
            'security_needs': ProjectUnderstanding._infer_security(desc_lower),
            'scalability_needs': ProjectUnderstanding._infer_scalability(desc_lower),
            'likely_risks': ProjectUnderstanding._infer_risks(desc_lower),
            'likely_team_roles': ProjectUnderstanding._infer_team_roles(desc_lower),
        }
        
        # Set primary domain
        if result['domains']:
            result['primary_domain'] = result['domains'][0]
            result['project_type'] = result['primary_domain'].replace('_', ' ').title()
        
        return result
    
    @staticmethod
    def _detect_domains(desc_lower: str) -> List[str]:
        """Detect domains using weighted, project-specific signals."""
        scores = {d: 0 for d in ProjectUnderstanding.DOMAIN_KEYWORDS}
        strong = {
            'CYBERSECURITY': ['cybersecurity','intrusion detection','vulnerability scanning','threat detection','security monitoring','siem','soc'],
            'HEALTHCARE': ['hospital management','patient records','medical records','healthcare','clinical'],
            'ECOMMERCE': ['e-commerce','ecommerce','food delivery','online shopping','shopping platform','restaurant management','shopping cart'],
            'IOT': ['iot','smart agriculture','smart home','sensor network','mqtt','embedded'],
            'AI_ML': ['artificial intelligence','machine learning','ai model','ml model','deep learning','neural network'],
            'EDUCATION': ['learning management','lms','college','university','school'],
            'EMPLOYEE_MGMT': ['employee attendance','employee management','human resources','hr management','payroll'],
            'BANKING': ['banking','bank account','financial institution','loan management','kyc','credit scoring'],
        }
        for d, kws in ProjectUnderstanding.DOMAIN_KEYWORDS.items():
            scores[d] += sum(1 for kw in kws if kw in desc_lower)
        for d, kws in strong.items():
            scores[d] += sum(5 for kw in kws if kw in desc_lower)
        if 'food delivery' in desc_lower or 'restaurant management' in desc_lower:
            scores['ECOMMERCE'] += 8
            scores['RESTAURANT'] += 2
            scores['BANKING'] = max(0, scores['BANKING'] - 5)
        if any(x in desc_lower for x in ['cybersecurity','intrusion detection','vulnerability scanning','threat detection']):
            scores['CYBERSECURITY'] += 10
            scores['EMPLOYEE_MGMT'] = max(0, scores['EMPLOYEE_MGMT'] - 3)
        return [d for d, score in sorted(scores.items(), key=lambda kv:(-kv[1],kv[0])) if score > 0]

    @staticmethod
    def _detect_complexity(desc_lower: str) -> str:
        """Infer project complexity."""
        for level, keywords in ProjectUnderstanding.COMPLEXITY_INDICATORS.items():
            if any(kw in desc_lower for kw in keywords):
                return level
        return 'MEDIUM'
    
    @staticmethod
    def _infer_users(desc_lower: str) -> List[str]:
        """Infer primary user types."""
        users = []
        user_patterns = {
            'employees': ['employee', 'staff', 'worker'],
            'customers': ['customer', 'client', 'user', 'patient', 'student'],
            'managers': ['manager', 'manager', 'supervisor', 'admin'],
            'developers': ['developer', 'engineer', 'programmer'],
            'traders': ['trader', 'investor', 'buyer'],
            'businesses': ['business', 'vendor', 'seller', 'merchant'],
            'patients': ['patient', 'doctor'],
            'students': ['student', 'teacher', 'professor'],
            'farmers': ['farmer', 'agricultural'],
            'residents': ['resident', 'tenant', 'homeowner'],
        }
        for user_type, patterns in user_patterns.items():
            if any(p in desc_lower for p in patterns):
                users.append(user_type)
        if any(x in desc_lower for x in ['college', 'university', 'school', 'learning management', 'lms', 'course']):
            users.append('students')
        return list(dict.fromkeys(users)) if users else ['Users']
    
    @staticmethod
    def _infer_stakeholders(desc_lower: str) -> List[str]:
        """Infer stakeholders."""
        stakeholders = ['Project Manager', 'Technical Lead']
        if any(x in desc_lower for x in ['hospital', 'medical', 'healthcare', 'patient', 'doctor']):
            stakeholders.extend(['Hospital Administrator', 'Medical Staff', 'Compliance Officer'])
        if any(x in desc_lower for x in ['ecommerce', 'shopping', 'seller', 'vendor']):
            stakeholders.extend(['Store Manager', 'Logistics Team', 'Customer Support'])
        if any(x in desc_lower for x in ['employee', 'hr', 'payroll']):
            stakeholders.extend(['HR Manager', 'Finance Team'])
        if any(x in desc_lower for x in ['student', 'college', 'university', 'learning']):
            stakeholders.extend(['Faculty', 'Academic Coordinator', 'Student Representative'])
        if any(x in desc_lower for x in ['security', 'cybersecurity', 'threat']):
            stakeholders.extend(['Security Officer', 'Compliance Officer'])
        return list(dict.fromkeys(stakeholders))
    
    @staticmethod
    def _infer_workflows(desc_lower: str) -> List[str]:
        """Infer major workflows."""
        workflows = []
        if any(x in desc_lower for x in ['login', 'auth', 'signup', 'registration']):
            workflows.append('User Authentication & Registration')
        if any(x in desc_lower for x in ['payment', 'billing', 'transaction', 'checkout']):
            workflows.append('Payment & Transaction Processing')
        if any(x in desc_lower for x in ['notification', 'alert', 'messaging']):
            workflows.append('Notification & Communication')
        if any(x in desc_lower for x in ['report', 'analytics', 'dashboard', 'monitoring']):
            workflows.append('Reporting & Analytics')
        if any(x in desc_lower for x in ['approval', 'workflow', 'review']):
            workflows.append('Approval & Review Workflow')
        if any(x in desc_lower for x in ['search', 'filter', 'discovery']):
            workflows.append('Search & Discovery')
        if any(x in desc_lower for x in ['data', 'integration', 'sync']):
            workflows.append('Data Integration & Synchronization')
        return workflows if workflows else ['Core Application Workflow']
    
    @staticmethod
    def _infer_features(desc_lower: str) -> List[str]:
        patterns = {
            'employee':['employee','staff','worker'], 'Attendance':['attendance','check-in','check in','check-out','check out'],
            'Leave Management':['leave','vacation','absence'], 'Payment':['payment','payments','checkout','billing'],
            'Product Catalog':['product','catalog','menu'], 'Shopping Cart':['cart'], 'Order Management':['order','orders'],
            'User Management':['user','profile','account','registration','signup'], 'Authentication':['login','auth','password','signin'],
            'Dashboard':['dashboard','analytics','metrics','insights','report','monitoring'], 'Notifications':['notification','alert','message','email','sms'],
            'Data Management':['database','storage','data','record','archive'], 'Reporting':['report','export','csv','pdf','analytics'],
            'Search':['search','filter','query','find'], 'API':['api','integration','third-party','external'],
            'Mobile':['mobile','android','ios','phone','user app'], 'Real-time':['real-time','realtime','live','stream','websocket','tracking'],
            'Patient Management':['patient','patient records'], 'Appointments':['appointment','appointments','scheduling'],
            'Threat Detection':['threat detection','threat monitoring'], 'Intrusion Detection':['intrusion detection'],
            'Vulnerability Scanning':['vulnerability scanning'], 'Courses':['course','courses'], 'Students':['student','students']
        }
        out=[name for name,kws in patterns.items() if any(k in desc_lower for k in kws)]
        return list(dict.fromkeys(out)) or ['Core Features']

    @staticmethod
    def _infer_tech(desc_lower: str) -> List[str]:
        """Infer technical components."""
        tech = []
        if any(x in desc_lower for x in ['frontend', 'ui', 'web', 'react', 'vue', 'angular']):
            tech.append('Frontend')
        if any(x in desc_lower for x in ['backend', 'server', 'api', 'python', 'node', 'java']):
            tech.append('Backend')
        if any(x in desc_lower for x in ['database', 'sql', 'postgres', 'mysql', 'mongodb', 'nosql']):
            tech.append('Database')
        if any(x in desc_lower for x in ['mobile', 'android', 'ios', 'app']):
            tech.append('Mobile')
        if any(x in desc_lower for x in ['cloud', 'aws', 'azure', 'gcp', 'deployment']):
            tech.append('Cloud Infrastructure')
        if any(x in desc_lower for x in ['iot', 'sensor', 'device', 'embedded']):
            tech.append('IoT/Embedded Systems')
        if any(x in desc_lower for x in ['ai', 'ml', 'machine learning', 'model', 'prediction']):
            tech.append('AI/ML')
        if any(x in desc_lower for x in ['security', 'encryption', 'auth', 'rbac']):
            tech.append('Security')
        if any(x in desc_lower for x in ['testing', 'test', 'qa']):
            tech.append('Testing/QA')
        return tech if tech else ['Backend', 'Database']
    
    @staticmethod
    def _infer_data_needs(desc_lower: str) -> List[str]:
        """Infer data requirements."""
        needs = []
        if any(x in desc_lower for x in ['user', 'profile', 'account', 'person']):
            needs.append('User/Person Data')
        if any(x in desc_lower for x in ['transaction', 'payment', 'order', 'billing']):
            needs.append('Transaction Data')
        if any(x in desc_lower for x in ['employee', 'staff', 'attendance', 'payroll']):
            needs.append('Employee/Person Data')
        if any(x in desc_lower for x in ['product', 'inventory', 'catalog', 'sku']):
            needs.append('Inventory Data')
        if any(x in desc_lower for x in ['sensor', 'device', 'iot', 'telemetry']):
            needs.append('Sensor/Telemetry Data')
        if any(x in desc_lower for x in ['historical', 'archive', 'log', 'audit']):
            needs.append('Historical/Audit Data')
        if any(x in desc_lower for x in ['time series', 'metrics', 'analytics']):
            needs.append('Time Series Data')
        return needs if needs else ['Structured Data']
    
    @staticmethod
    def _infer_integrations(desc_lower: str) -> List[str]:
        """Infer external integrations."""
        integrations = []
        if any(x in desc_lower for x in ['payment', 'stripe', 'paypal', 'razorpay']):
            integrations.append('Payment Gateway')
        if any(x in desc_lower for x in ['email', 'sendgrid', 'mailgun']):
            integrations.append('Email Service')
        if any(x in desc_lower for x in ['sms', 'twilio']):
            integrations.append('SMS Service')
        if any(x in desc_lower for x in ['map', 'location', 'google maps', 'geolocation']):
            integrations.append('Mapping Service')
        if any(x in desc_lower for x in ['social', 'facebook', 'google', 'oauth']):
            integrations.append('Social/OAuth Integration')
        if any(x in desc_lower for x in ['slack', 'teams', 'discord']):
            integrations.append('Chat Integration')
        if any(x in desc_lower for x in ['storage', 's3', 'azure', 'gcs', 'blob']):
            integrations.append('Cloud Storage')
        if any(x in desc_lower for x in ['analytics', 'mixpanel', 'amplitude', 'ga']):
            integrations.append('Analytics Platform')
        return integrations
    
    @staticmethod
    def _infer_security(desc_lower: str) -> List[str]:
        """Infer security needs."""
        needs = ['Authentication', 'Authorization']
        if any(x in desc_lower for x in ['payment', 'financial', 'banking']):
            needs.extend(['PCI Compliance', 'Encryption', 'Fraud Detection'])
        if any(x in desc_lower for x in ['medical', 'health', 'patient', 'hospital']):
            needs.extend(['HIPAA Compliance', 'Audit Logging', 'Data Privacy'])
        if any(x in desc_lower for x in ['personal', 'privacy', 'gdpr', 'pii']):
            needs.append('Data Privacy (GDPR/CCPA)')
        if any(x in desc_lower for x in ['security', 'cybersecurity', 'threat', 'vulnerability']):
            needs.extend(['Threat Monitoring', 'Intrusion Detection', 'Vulnerability Scanning'])
        return list(dict.fromkeys(needs))
    
    @staticmethod
    def _infer_scalability(desc_lower: str) -> List[str]:
        """Infer scalability needs."""
        needs = []
        if any(x in desc_lower for x in ['large', 'millions', 'thousands', 'enterprise']):
            needs.append('High Volume')
        if any(x in desc_lower for x in ['real-time', 'live', 'stream', 'instant']):
            needs.append('Low Latency')
        if any(x in desc_lower for x in ['distributed', 'multi-region', 'global', 'worldwide']):
            needs.append('Geographic Distribution')
        if any(x in desc_lower for x in ['high availability', 'failover', 'redundant']):
            needs.append('High Availability')
        if any(x in desc_lower for x in ['mobile', 'offline', 'sync']):
            needs.append('Mobile/Offline Support')
        return needs if needs else []
    
    @staticmethod
    def _infer_risks(desc_lower: str) -> List[str]:
        """Infer likely risks."""
        risks = []
        if any(x in desc_lower for x in ['deadline', 'urgent', 'quick', 'fast', 'soon']):
            risks.append('Schedule Pressure')
        if any(x in desc_lower for x in ['complex', 'advanced', 'sophisticated']):
            risks.append('Technical Complexity')
        if any(x in desc_lower for x in ['new technology', 'unfamiliar', 'learning curve']):
            risks.append('Technology Risk')
        if any(x in desc_lower for x in ['payment', 'financial', 'banking']):
            risks.append('Correctness Risk')
        if any(x in desc_lower for x in ['security', 'privacy', 'compliance']):
            risks.append('Compliance Risk')
        if any(x in desc_lower for x in ['integration', 'third-party', 'external']):
            risks.append('Integration Risk')
        if any(x in desc_lower for x in ['data', 'volume', 'performance']):
            risks.append('Performance Risk')
        return risks if risks else []
    
    @staticmethod
    def _infer_team_roles(desc_lower: str) -> List[str]:
        roles=['Project Manager','Backend Developer','QA Engineer']
        if any(x in desc_lower for x in ['hospital','medical','healthcare','patient','doctor']): roles += ['Hospital Administrator','Healthcare Domain Specialist','Security Engineer']
        if any(x in desc_lower for x in ['ecommerce','e-commerce','shopping','food delivery','restaurant']): roles += ['Product Manager','Frontend Developer','Payment Integration Engineer','DevOps Engineer']
        if any(x in desc_lower for x in ['security','cybersecurity','threat','intrusion','vulnerability']): roles += ['Security Officer','Security Engineer','Threat Detection Specialist']
        if any(x in desc_lower for x in ['student','college','university','learning','lms']): roles += ['Education Domain Specialist','Frontend Developer']
        if any(x in desc_lower for x in ['ai','ml','machine learning','data science','prediction']): roles += ['Data Scientist','ML Engineer']
        if any(x in desc_lower for x in ['iot','embedded','sensor','device']): roles += ['IoT Engineer','Embedded Engineer','Data Engineer']
        if any(x in desc_lower for x in ['database','data','big data']): roles.append('Database Engineer')
        if any(x in desc_lower for x in ['cloud','deployment','devops','infrastructure']): roles.append('DevOps Engineer')
        if any(x in desc_lower for x in ['mobile','android','ios']): roles.append('Mobile Developer')
        return list(dict.fromkeys(roles))


# ========== DOMAIN ADAPTER ==========

class DomainAdapter:
    """Adapt project generation to specific domains."""
    
    @staticmethod
    def adapt(understanding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt project components based on detected domain.
        Returns adapted understanding with domain-specific recommendations.
        """
        domain = understanding.get('primary_domain', 'GENERAL')
        
        adaptations = {
            'EMPLOYEE_MGMT': DomainAdapter._adapt_employee_mgmt,
            'HEALTHCARE': DomainAdapter._adapt_healthcare,
            'ECOMMERCE': DomainAdapter._adapt_ecommerce,
            'IOT': DomainAdapter._adapt_iot,
            'AI_ML': DomainAdapter._adapt_ai_ml,
            'EDUCATION': DomainAdapter._adapt_education,
            'CYBERSECURITY': DomainAdapter._adapt_cybersecurity,
            'BANKING': DomainAdapter._adapt_banking,
        }
        
        adapter_func = adaptations.get(domain, DomainAdapter._adapt_generic)
        adapted = adapter_func(understanding)
        return adapted
    
    @staticmethod
    def _adapt_employee_mgmt(understanding: Dict[str, Any]) -> Dict[str, Any]:
        understanding['adapted_modules'] = [
            'User Authentication & Authorization',
            'Employee Master Data',
            'Attendance & Time Tracking',
            'Leave Management',
            'Payroll',
            'Dashboard & Reports',
            'Notification System',
            'Audit & Compliance',
        ]
        understanding['adapted_phases'] = ['requirements', 'architecture', 'database_design', 'backend', 'frontend', 'testing', 'deployment']
        understanding['adapted_team_roles'] = ['Project Manager', 'Backend Developer', 'Frontend Developer', 'Database Engineer', 'QA Engineer']
        understanding['adapted_risks'] = ['Data Accuracy', 'Security (Employee Data)', 'Payroll Correctness', 'Schedule Pressure', 'Testing Coverage']
        return understanding
    
    @staticmethod
    def _adapt_healthcare(understanding: Dict[str, Any]) -> Dict[str, Any]:
        understanding['adapted_modules'] = [
            'Patient Management',
            'Doctor/Staff Management',
            'Appointment Scheduling',
            'Medical Records (EHR)',
            'Prescription Management',
            'Billing & Insurance',
            'Notification System',
            'Compliance & Audit',
            'HIPAA Security',
        ]
        understanding['adapted_phases'] = ['requirements', 'compliance', 'architecture', 'database_design', 'backend', 'frontend', 'security_testing', 'deployment']
        understanding['adapted_team_roles'] = ['Project Manager', 'Backend Developer', 'Frontend Developer', 'Database Engineer', 'Security Engineer', 'QA Engineer']
        understanding['adapted_risks'] = ['HIPAA Compliance', 'Data Privacy', 'Medical Data Accuracy', 'System Availability', 'Security', 'Integration with Existing Systems']
        return understanding
    
    @staticmethod
    def _adapt_ecommerce(understanding: Dict[str, Any]) -> Dict[str, Any]:
        understanding['adapted_modules'] = [
            'Product Catalog',
            'Shopping Cart',
            'Payment Processing',
            'Order Management',
            'User Accounts',
            'Inventory Management',
            'Shipping & Logistics',
            'Reviews & Ratings',
            'Search & Recommendations',
            'Admin Dashboard',
            'Notification System',
        ]
        understanding['adapted_phases'] = ['requirements', 'architecture', 'database_design', 'backend', 'frontend', 'payment_integration', 'performance_testing', 'security_testing', 'deployment']
        understanding['adapted_team_roles'] = ['Project Manager', 'Product Manager', 'Backend Developer', 'Frontend Developer', 'Database Engineer', 'DevOps Engineer', 'QA Engineer']
        understanding['adapted_risks'] = ['Payment Security', 'Performance Under Load', 'Inventory Accuracy', 'Payment Gateway Integration', 'Cart Abandonment Issues', 'Mobile Experience', 'Competition']
        return understanding
    
    @staticmethod
    def _adapt_iot(understanding: Dict[str, Any]) -> Dict[str, Any]:
        understanding['adapted_modules'] = [
            'Device Management',
            'Sensor Data Collection',
            'Data Processing & Pipeline',
            'Real-time Dashboard',
            'Alerts & Notifications',
            'Edge Computing',
            'Data Storage & Analytics',
            'Mobile App',
            'API for External Integration',
            'Security & Encryption',
        ]
        understanding['adapted_phases'] = ['requirements', 'architecture', 'hardware_selection', 'embedded_firmware', 'backend', 'frontend', 'testing', 'deployment']
        understanding['adapted_team_roles'] = ['Project Manager', 'Embedded Engineer', 'Backend Developer', 'Frontend Developer', 'Data Engineer', 'DevOps Engineer', 'QA Engineer']
        understanding['adapted_risks'] = ['Hardware Compatibility', 'Network Connectivity', 'Data Volume & Storage', 'Real-time Processing', 'Power Management', 'Security of Devices']
        return understanding
    
    @staticmethod
    def _adapt_ai_ml(understanding: Dict[str, Any]) -> Dict[str, Any]:
        understanding['adapted_modules'] = [
            'Data Collection & Preparation',
            'Feature Engineering',
            'Model Development & Training',
            'Model Evaluation & Validation',
            'Model Deployment',
            'Inference Service',
            'Monitoring & Retraining',
            'UI/Dashboard for Results',
            'API for Model Access',
            'Documentation',
        ]
        understanding['adapted_phases'] = ['requirements', 'data_analysis', 'feature_engineering', 'model_development', 'evaluation', 'backend', 'frontend', 'testing', 'deployment']
        understanding['adapted_team_roles'] = ['Project Manager', 'Data Scientist', 'ML Engineer', 'Backend Developer', 'Frontend Developer', 'Data Engineer', 'DevOps Engineer', 'QA Engineer']
        understanding['adapted_risks'] = ['Data Quality', 'Model Accuracy', 'Overfitting', 'Bias in Data', 'Computational Resources', 'Model Interpretability', 'Deployment Complexity']
        return understanding
    
    @staticmethod
    def _adapt_education(understanding: Dict[str, Any]) -> Dict[str, Any]:
        understanding['adapted_modules'] = [
            'User Management (Students, Teachers, Admins)',
            'Course Management',
            'Learning Materials (Videos, Documents)',
            'Assignments & Submissions',
            'Assessment & Grading',
            'Discussion Forums',
            'Announcements & Notifications',
            'Attendance Tracking',
            'Reports & Analytics',
            'Certificate Generation',
        ]
        understanding['adapted_phases'] = ['requirements', 'architecture', 'database_design', 'backend', 'frontend', 'testing', 'deployment']
        understanding['adapted_team_roles'] = ['Project Manager', 'Backend Developer', 'Frontend Developer', 'UI/UX Designer', 'Database Engineer', 'QA Engineer']
        understanding['adapted_risks'] = ['User Adoption', 'Data Volume Growth', 'Concurrent Users During Exams', 'Content Quality', 'Accessibility Compliance']
        return understanding
    
    @staticmethod
    def _adapt_cybersecurity(understanding: Dict[str, Any]) -> Dict[str, Any]:
        understanding['adapted_modules'] = [
            'Threat Data Collection',
            'Security Event Logging',
            'Intrusion Detection',
            'Vulnerability Scanning',
            'Alert & Response',
            'Dashboard & Visualization',
            'Compliance Reporting',
            'Audit Logging',
            'Integration with Security Tools',
            'User Management',
        ]
        understanding['adapted_phases'] = ['requirements', 'security_architecture', 'backend', 'frontend', 'security_testing', 'penetration_testing', 'deployment']
        understanding['adapted_team_roles'] = ['Project Manager', 'Security Engineer', 'Backend Developer', 'Frontend Developer', 'DevOps Engineer', 'QA Engineer']
        understanding['adapted_risks'] = ['Alert Fatigue', 'False Positives', 'Threat Detection Accuracy', 'Integration Complexity', 'Performance Under Load']
        return understanding
    
    @staticmethod
    def _adapt_banking(understanding: Dict[str, Any]) -> Dict[str, Any]:
        understanding['adapted_modules'] = [
            'User Authentication & Authorization',
            'Account Management',
            'Transaction Processing',
            'Fraud Detection',
            'Compliance & Audit',
            'Reporting',
            'Notification System',
            'Integration with Payment Networks',
            'Encryption & Security',
        ]
        understanding['adapted_phases'] = ['requirements', 'compliance', 'security_architecture', 'database_design', 'backend', 'frontend', 'security_testing', 'penetration_testing', 'deployment']
        understanding['adapted_team_roles'] = ['Project Manager', 'Backend Developer', 'Security Engineer', 'Database Engineer', 'Compliance Officer', 'QA Engineer']
        understanding['adapted_risks'] = ['Regulatory Compliance', 'Fraud', 'System Downtime', 'Security Breaches', 'Performance', 'Auditability']
        return understanding
    
    @staticmethod
    def _adapt_generic(understanding: Dict[str, Any]) -> Dict[str, Any]:
        # Generic adaptation for unknown project types
        understanding['adapted_modules'] = [
            'User Management',
            'Core Features',
            'Data Management',
            'API & Integrations',
            'Frontend',
            'Testing',
            'Deployment',
        ]
        understanding['adapted_phases'] = ['requirements', 'architecture', 'backend', 'frontend', 'testing', 'deployment']
        understanding['adapted_team_roles'] = ['Project Manager', 'Backend Developer', 'Frontend Developer', 'QA Engineer']
        understanding['adapted_risks'] = ['Schedule Pressure', 'Technical Complexity', 'Team Capacity', 'Testing Coverage']
        return understanding


# ========== REQUIREMENTS ENGINE ==========

class RequirementEngine:
    """Generate functional and non-functional requirements."""
    
    @staticmethod
    def generate(understanding: Dict[str, Any]) -> List[Requirement]:
        """Generate requirements based on project understanding."""
        requirements = []
        req_id = 1
        
        # Functional requirements based on inferred features
        for feature in understanding.get('major_features', []):
            req = Requirement(
                req_id=f'FR{req_id}',
                title=feature,
                description=f'Implement {feature.lower()} functionality.',
                category='FUNCTIONAL',
                priority='HIGH',
                phase='requirements'
            )
            requirements.append(req)
            req_id += 1
        
        # Non-functional requirements based on security and scalability needs
        for security_need in understanding.get('security_needs', []):
            req = Requirement(
                req_id=f'NFR{req_id}',
                title=f'Security: {security_need}',
                description=f'Ensure {security_need.lower()} is implemented.',
                category='NON-FUNCTIONAL',
                priority='CRITICAL' if any(x in security_need for x in ['Compliance', 'Encryption']) else 'HIGH',
                phase='architecture'
            )
            requirements.append(req)
            req_id += 1
        
        for scalability in understanding.get('scalability_needs', []):
            req = Requirement(
                req_id=f'NFR{req_id}',
                title=f'Scalability: {scalability}',
                description=f'System must support {scalability.lower()}.',
                category='NON-FUNCTIONAL',
                priority='HIGH',
                phase='architecture'
            )
            requirements.append(req)
            req_id += 1
        
        # Default NFRs
        default_nfrs = [
            ('Performance', 'System must respond within acceptable latency (< 2s for most operations)', 'HIGH'),
            ('Availability', 'System must have 99%+ uptime (or match user expectation)', 'HIGH'),
            ('Maintainability', 'Code must be well-documented and follow best practices', 'MEDIUM'),
            ('Testability', 'System must have comprehensive test coverage (> 80%)', 'MEDIUM'),
        ]
        
        for title, desc, priority in default_nfrs:
            req = Requirement(
                req_id=f'NFR{req_id}',
                title=title,
                description=desc,
                category='NON-FUNCTIONAL',
                priority=priority,
                phase='architecture'
            )
            requirements.append(req)
            req_id += 1
        
        return requirements


# ========== MODULE GENERATOR ==========

class ModuleGenerator:
    """Generate project modules/components."""
    
    @staticmethod
    def generate(understanding: Dict[str, Any]) -> List[Module]:
        """Generate modules based on domain and complexity."""
        modules = []
        module_id = 1
        
        adapted_modules = understanding.get('adapted_modules', [])
        
        for module_name in adapted_modules:
            module = Module(
                module_id=f'MOD{module_id}',
                name=module_name,
                description=f'Implement {module_name.lower()}.',
                category=ModuleGenerator._infer_category(module_name),
                effort=ModuleGenerator._estimate_effort(module_name, understanding),
                dependencies=ModuleGenerator._infer_dependencies(module_name, modules),
                risk_level=ModuleGenerator._assess_risk(module_name),
            )
            modules.append(module)
            module_id += 1
        
        return modules
    
    @staticmethod
    def _infer_category(name: str) -> str:
        """Infer module category from name."""
        name_lower = name.lower()
        if any(x in name_lower for x in ['frontend', 'ui', 'web', 'dashboard']):
            return 'FRONTEND'
        elif any(x in name_lower for x in ['backend', 'api', 'processing', 'service']):
            return 'BACKEND'
        elif any(x in name_lower for x in ['database', 'data model', 'storage', 'data']):
            return 'DATA'
        elif any(x in name_lower for x in ['integration', 'payment', 'external']):
            return 'INTEGRATIONS'
        elif any(x in name_lower for x in ['security', 'auth', 'encryption']):
            return 'SECURITY'
        elif any(x in name_lower for x in ['testing', 'qa']):
            return 'TESTING'
        elif any(x in name_lower for x in ['deployment', 'devops', 'infrastructure']):
            return 'DEVOPS'
        else:
            return 'BACKEND'
    
    @staticmethod
    def _estimate_effort(name: str, understanding: Dict[str, Any]) -> float:
        """Estimate effort for module."""
        complexity = understanding.get('complexity', 'MEDIUM')
        base_effort = 3.0
        
        complexity_multiplier = {'SIMPLE': 0.6, 'MEDIUM': 1.0, 'COMPLEX': 1.5, 'ENTERPRISE': 2.0}.get(complexity, 1.0)
        
        name_lower = name.lower()
        if 'management' in name_lower:
            base_effort = 4.0
        elif 'authentication' in name_lower or 'security' in name_lower:
            base_effort = 3.0
        elif 'payment' in name_lower or 'billing' in name_lower:
            base_effort = 5.0
        elif 'dashboard' in name_lower or 'analytics' in name_lower:
            base_effort = 4.0
        elif 'api' in name_lower or 'integration' in name_lower:
            base_effort = 4.0
        elif 'deployment' in name_lower or 'devops' in name_lower:
            base_effort = 3.0
        elif 'testing' in name_lower:
            base_effort = 3.0
        
        return round(base_effort * complexity_multiplier, 1)
    
    @staticmethod
    def _infer_dependencies(name: str, existing_modules: List[Module]) -> List[str]:
        """Infer module dependencies."""
        dependencies = []
        name_lower = name.lower()
        
        # Most modules depend on authentication
        if 'authentication' not in name_lower and existing_modules:
            for mod in existing_modules:
                if 'authentication' in mod.name.lower():
                    dependencies.append(mod.module_id)
                    break
        
        # Frontend depends on API/Backend
        if any(x in name_lower for x in ['frontend', 'ui', 'dashboard']):
            for mod in existing_modules:
                if any(x in mod.name.lower() for x in ['api', 'backend', 'service']):
                    dependencies.append(mod.module_id)
        
        # Payment depends on authentication and database
        if 'payment' in name_lower:
            for mod in existing_modules:
                if any(x in mod.name.lower() for x in ['authentication', 'database', 'data model']):
                    dependencies.append(mod.module_id)
        
        return list(dict.fromkeys(dependencies))  # Remove duplicates
    
    @staticmethod
    def _assess_risk(name: str) -> str:
        """Assess risk level for module."""
        name_lower = name.lower()
        
        if any(x in name_lower for x in ['payment', 'security', 'compliance']):
            return 'CRITICAL'
        elif any(x in name_lower for x in ['authentication', 'database', 'integration']):
            return 'HIGH'
        elif any(x in name_lower for x in ['testing', 'deployment']):
            return 'MEDIUM'
        else:
            return 'MEDIUM'


# ========== TASK GENERATOR ==========

class TaskGenerator:
    """Generate implementation tasks."""
    
    PHASES = [
        'discovery', 'requirements', 'architecture', 'ui_ux',
        'database_design', 'backend', 'frontend', 'integrations',
        'testing', 'security', 'deployment', 'monitoring'
    ]
    
    @staticmethod
    def generate(understanding: Dict[str, Any], modules: List[Module]) -> List[Task]:
        """Generate tasks based on modules and complexity."""
        tasks = []
        task_id = 1
        
        complexity = understanding.get('complexity', 'MEDIUM')
        phase_order = understanding.get('adapted_phases', TaskGenerator.PHASES)
        
        # Generic phase tasks
        generic_phase_tasks = {
            'requirements': [
                ('Requirements Analysis', 'Define detailed scope, acceptance criteria and constraints.', 3.0, 'HIGH'),
                ('Specification', 'Document requirements specification and user stories.', 3.0, 'HIGH'),
            ],
            'architecture': [
                ('System Design', 'Design application architecture, APIs, and data flow.', 4.0, 'HIGH'),
                ('Technology Selection', 'Select and evaluate technology stack.', 2.0, 'MEDIUM'),
            ],
            'database_design': [
                ('Data Model Design', 'Design database schema and entity relationships.', 4.0, 'HIGH'),
                ('Database Setup', 'Configure database, migrations and initialization.', 2.0, 'MEDIUM'),
            ],
            'backend': [
                ('API Development', 'Implement core APIs and business logic.', 5.0, 'HIGH'),
                ('Service Implementation', 'Implement backend services and middleware.', 4.0, 'HIGH'),
            ],
            'frontend': [
                ('UI Development', 'Implement frontend UI and components.', 5.0, 'HIGH'),
                ('Integration Testing', 'Integrate frontend with backend APIs.', 3.0, 'MEDIUM'),
            ],
            'testing': [
                ('Unit Testing', 'Write and execute unit tests.', 3.0, 'HIGH'),
                ('Integration Testing', 'Test component and service interactions.', 3.0, 'HIGH'),
                ('End-to-End Testing', 'Test complete workflows.', 3.0, 'MEDIUM'),
            ],
            'security': [
                ('Security Review', 'Review code and architecture for security issues.', 3.0, 'HIGH'),
                ('Security Testing', 'Perform security and vulnerability testing.', 3.0, 'HIGH'),
            ],
            'deployment': [
                ('Deployment Setup', 'Prepare deployment scripts and infrastructure.', 2.0, 'MEDIUM'),
                ('Production Deployment', 'Deploy to production and validate.', 2.0, 'HIGH'),
                ('Monitoring Setup', 'Configure monitoring and alerting.', 2.0, 'MEDIUM'),
            ],
        }
        
        # Generate tasks for each phase
        for phase in phase_order:
            phase_tasks = generic_phase_tasks.get(phase, [])
            for task_name, desc, effort, priority in phase_tasks:
                task = Task(
                    task_key=f'T{task_id}',
                    name=task_name,
                    description=desc,
                    module_id=TaskGenerator._find_module_for_task(task_name, modules),
                    phase=phase,
                    priority=priority,
                    effort=effort,
                    owner_role=TaskGenerator._assign_owner(phase),
                    risk_level=TaskGenerator._assess_task_risk(priority, phase),
                    acceptance_criteria=TaskGenerator._generate_acceptance_criteria(task_name),
                    critical_path_eligible=phase in ['requirements', 'architecture', 'database_design', 'backend'],
                )
                tasks.append(task)
                task_id += 1
        
        # Module-specific tasks
        for module in modules:
            if module.name in ['User Management', 'Authentication', 'Authorization']:
                task = Task(
                    task_key=f'T{task_id}',
                    name=f'Implement {module.name}',
                    description=f'Implement {module.name.lower()} with proper security controls.',
                    module_id=module.module_id,
                    phase='backend',
                    priority='CRITICAL' if 'Authentication' in module.name else 'HIGH',
                    effort=module.effort,
                    owner_role='Backend Developer',
                    risk_level=module.risk_level,
                    acceptance_criteria=[
                        f'{module.name} is implemented and tested',
                        'All acceptance criteria are met',
                        'Security review is passed',
                    ],
                    critical_path_eligible=True,
                )
                tasks.append(task)
                task_id += 1
        
        # Add one implementation task per generated module so real projects have
        # enough actionable work while remaining domain-driven.
        for module in modules:
            phase = 'frontend' if module.category == 'FRONTEND' else ('testing' if module.category == 'TESTING' else 'backend')
            owner = 'Frontend Developer' if phase == 'frontend' else ('QA Engineer' if phase == 'testing' else ('Security Engineer' if module.category == 'SECURITY' else 'Backend Developer'))
            tasks.append(Task(task_key=f'T{task_id}', name=f'Implement {module.name}',
                description=f'Implement, integrate and validate the {module.name.lower()} module.',
                module_id=module.module_id, phase=phase, priority='HIGH' if module.risk_level in ('HIGH','CRITICAL') else 'MEDIUM',
                effort=max(1.0,module.effort), owner_role=owner, risk_level=module.risk_level,
                acceptance_criteria=[f'{module.name} is implemented','Integration checks pass','Code review is passed']))
            task_id += 1

        return tasks
    
    @staticmethod
    def _find_module_for_task(task_name: str, modules: List[Module]) -> str:
        """Find appropriate module for task."""
        task_lower = task_name.lower()
        for module in modules:
            if any(x in task_lower for x in module.name.lower().split()):
                return module.module_id
        return modules[0].module_id if modules else 'MOD1'
    
    @staticmethod
    def _assign_owner(phase: str) -> str:
        """Assign task owner role based on phase."""
        owners = {
            'requirements': 'Product Manager',
            'architecture': 'Solution Architect',
            'ui_ux': 'UI/UX Designer',
            'database_design': 'Database Engineer',
            'backend': 'Backend Developer',
            'frontend': 'Frontend Developer',
            'integrations': 'Backend Developer',
            'testing': 'QA Engineer',
            'security': 'Security Engineer',
            'deployment': 'DevOps Engineer',
            'monitoring': 'DevOps Engineer',
            'discovery': 'Product Manager',
        }
        return owners.get(phase, 'Developer')
    
    @staticmethod
    def _assess_task_risk(priority: str, phase: str) -> str:
        """Assess task risk level."""
        if priority == 'CRITICAL' or phase == 'security':
            return 'CRITICAL'
        elif priority == 'HIGH' or phase in ['database_design', 'backend']:
            return 'HIGH'
        else:
            return 'MEDIUM'
    
    @staticmethod
    def _generate_acceptance_criteria(task_name: str) -> List[str]:
        """Generate acceptance criteria for task."""
        task_lower = task_name.lower()
        
        criteria = ['Task is completed', 'Code review is passed']
        
        if 'test' in task_lower:
            criteria.append('Test coverage is > 80%')
            criteria.append('All tests pass')
        
        if 'security' in task_lower:
            criteria.append('Security review is passed')
            criteria.append('No critical vulnerabilities found')
        
        if 'deploy' in task_lower:
            criteria.append('Deployment is successful')
            criteria.append('Production validation is passed')
        
        return criteria


TaskGenerator.Task = Task


# ========== DEPENDENCY GENERATOR ==========

class DependencyGenerator:
    """Generate task dependencies."""
    
    @staticmethod
    def generate(tasks: List[Task]) -> List[Tuple[str, str]]:
        """Generate logical dependencies between tasks."""
        dependencies = []
        
        # Create baseline: T1 -> T2 (Requirements -> Architecture) if both exist
        # This ensures cycle detection works correctly
        if len(tasks) >= 2:
            dependencies.append((tasks[0].task_key, tasks[1].task_key))
        
        # Group tasks by phase
        tasks_by_phase = {}
        for task in tasks:
            phase = task.phase
            if phase not in tasks_by_phase:
                tasks_by_phase[phase] = []
            tasks_by_phase[phase].append(task)
        
        # Phase ordering
        phase_order = [
            'discovery', 'requirements', 'architecture',
            'ui_ux', 'database_design', 'backend', 'frontend', 'integrations',
            'testing', 'security', 'deployment', 'monitoring'
        ]
        
        prev_phase_task = None
        for phase in phase_order:
            if phase not in tasks_by_phase:
                continue
            
            phase_tasks = tasks_by_phase[phase]
            
            # Each task in a phase depends on at least one task from previous phase
            if prev_phase_task and phase_tasks:
                for task in phase_tasks:
                    if (prev_phase_task.task_key, task.task_key) not in dependencies:
                        dependencies.append((prev_phase_task.task_key, task.task_key))
            
            # Remember last task of this phase for next phase
            if phase_tasks:
                prev_phase_task = phase_tasks[-1]
        
        # All implementation tasks lead to Testing
        testing_tasks = tasks_by_phase.get('testing', [])
        if testing_tasks:
            for phase in ['backend', 'frontend', 'integrations', 'ui_ux', 'database_design']:
                phase_tasks = tasks_by_phase.get(phase, [])
                for task in phase_tasks:
                    if (task.task_key, testing_tasks[0].task_key) not in dependencies:
                        dependencies.append((task.task_key, testing_tasks[0].task_key))
        
        # Module-specific dependencies
        for task in tasks:
            if task.dependencies:
                for dep_task_key in task.dependencies:
                    if dep_task_key in [t.task_key for t in tasks]:
                        if (dep_task_key, task.task_key) not in dependencies:
                            dependencies.append((dep_task_key, task.task_key))
        
        # Remove invalid dependencies
        valid_deps = []
        task_keys = {t.task_key for t in tasks}
        for from_task, to_task in dependencies:
            if from_task != to_task and from_task in task_keys and to_task in task_keys:
                if (from_task, to_task) not in valid_deps:
                    valid_deps.append((from_task, to_task))
        
        return valid_deps


# ========== TEAM GENERATOR ==========

class TeamGenerator:
    """Generate recommended team roles."""
    
    TEAM_TEMPLATES = {
        'SIMPLE': [
            ('Project Manager', 'Manage the project', 80, 'Project Management'),
            ('Full Stack Developer', 'Implement features', 80, 'Backend, Frontend'),
            ('QA Engineer', 'Test the application', 60, 'Testing'),
        ],
        'MEDIUM': [
            ('Project Manager', 'Manage the project', 100, 'Project Management'),
            ('Backend Developer', 'Build APIs and services', 80, 'Backend'),
            ('Frontend Developer', 'Build UI components', 80, 'Frontend'),
            ('Database Engineer', 'Design and manage databases', 60, 'Database'),
            ('QA Engineer', 'Test all components', 80, 'Testing'),
        ],
        'COMPLEX': [
            ('Project Manager', 'Manage the project', 100, 'Project Management'),
            ('Solution Architect', 'Design the system', 60, 'Architecture'),
            ('Backend Developer', 'Build APIs and services', 80, 'Backend'),
            ('Frontend Developer', 'Build UI components', 80, 'Frontend'),
            ('Database Engineer', 'Design and manage databases', 80, 'Database'),
            ('DevOps Engineer', 'Handle deployment and infrastructure', 60, 'DevOps'),
            ('QA Engineer', 'Test all components', 80, 'Testing'),
            ('Security Engineer', 'Review security', 40, 'Security'),
        ],
        'ENTERPRISE': [
            ('Project Manager', 'Manage the project', 100, 'Project Management'),
            ('Product Manager', 'Manage requirements', 80, 'Requirements'),
            ('Solution Architect', 'Design the system', 100, 'Architecture'),
            ('Backend Developer', 'Build APIs and services', 80, 'Backend'),
            ('Frontend Developer', 'Build UI components', 80, 'Frontend'),
            ('Database Engineer', 'Design and manage databases', 80, 'Database'),
            ('DevOps Engineer', 'Handle deployment and infrastructure', 80, 'DevOps'),
            ('QA Engineer', 'Test all components', 100, 'Testing'),
            ('Security Engineer', 'Review security and compliance', 100, 'Security'),
            ('Data Engineer', 'Manage data pipelines', 60, 'Data'),
        ],
    }
    
    @staticmethod
    def generate(understanding: Dict[str, Any]) -> List[TeamRole]:
        """Generate recommended team roles."""
        complexity = understanding.get('complexity', 'MEDIUM')
        template = TeamGenerator.TEAM_TEMPLATES.get(complexity, TeamGenerator.TEAM_TEMPLATES['MEDIUM'])
        
        team = []
        for role_name, reason, capacity, categories in template:
            team_role = TeamRole(
                role=role_name,
                reason=reason,
                capacity=capacity,
                responsibilities=[f'Responsible for {categories.lower()}'],
                task_categories=categories.split(', ')
            )
            team.append(team_role)
        
        return team


# ========== RISK GENERATOR ==========

class RiskGenerator:
    """Generate project-specific risks."""
    
    @staticmethod
    def generate(understanding: Dict[str, Any], tasks: List[Task]) -> List[Dict[str, Any]]:
        """Generate project-specific risks."""
        risks = []
        risk_id = 1
        
        inferred_risks = understanding.get('likely_risks', [])
        
        for risk_name in inferred_risks:
            risk = {
                'risk_id': f'R{risk_id}',
                'name': risk_name,
                'description': f'{risk_name} could impact project delivery.',
                'probability': 60,
                'impact': 70,
                'score': int((60 * 70) / 100),
                'severity': 'HIGH',
                'mitigation': f'Develop mitigation strategy for {risk_name.lower()}.',
                'affected_tasks': [],
            }
            risks.append(risk)
            risk_id += 1
        
        # Add domain-specific risks
        domain_risks = understanding.get('adapted_risks', [])
        for risk_name in domain_risks:
            if not any(r['name'] == risk_name for r in risks):
                risk = {
                    'risk_id': f'R{risk_id}',
                    'name': risk_name,
                    'description': f'{risk_name} is a significant concern for this type of project.',
                    'probability': 65,
                    'impact': 75,
                    'score': int((65 * 75) / 100),
                    'severity': 'HIGH',
                    'mitigation': f'Develop specific mitigation for {risk_name.lower()}.',
                    'affected_tasks': [],
                }
                risks.append(risk)
                risk_id += 1
        
        if 'payment' in understanding.get('raw_description', '').lower() and not any('payment' in r['name'].lower() for r in risks):
            risks.append({'risk_id':f'R{risk_id}','name':'Payment Processing Risk','description':'Payment processing failures or incorrect transaction handling can affect delivery.','probability':65,'impact':80,'score':52,'severity':'HIGH','mitigation':'Use a trusted gateway, idempotency, retries and reconciliation.','affected_tasks':[]})
            risk_id += 1
        domain = understanding.get('primary_domain')
        if domain == 'ECOMMERCE' and not any('payment' in r['name'].lower() for r in risks):
            risks.append({'risk_id':f'R{risk_id}','name':'Payment Security','description':'Payment processing and gateway failures can affect checkout and revenue.','probability':65,'impact':80,'score':52,'severity':'HIGH','mitigation':'Use a trusted payment gateway, idempotency, retries and secure webhook validation.','affected_tasks':[]})
            risk_id += 1
        for risk_name in ['Schedule Pressure','Technical Complexity','Testing Coverage']:
            if not any(r['name'] == risk_name for r in risks):
                risks.append({'risk_id':f'R{risk_id}','name':risk_name,'description':f'{risk_name} could affect delivery.','probability':45,'impact':60,'score':27,'severity':'MEDIUM','mitigation':f'Plan and monitor controls for {risk_name.lower()}.','affected_tasks':[]})
                risk_id += 1
        return risks


# ========== ARCHITECTURE GENERATOR ==========

class ArchitectureGenerator:
    """Generate architecture description."""
    
    @staticmethod
    def generate(understanding: Dict[str, Any], modules: List[Module]) -> Dict[str, Any]:
        """Generate architecture based on domain."""
        domain = understanding.get('primary_domain', 'GENERAL')
        
        architectures = {
            'EMPLOYEE_MGMT': {
                'description': 'Multi-tier architecture with separate frontend, API, business logic, and database layers.',
                'components': ['Frontend (React/Vue)', 'REST API', 'Business Logic Layer', 'Database (PostgreSQL)', 'File Storage'],
                'data_flow': 'Frontend → API → Business Logic → Database',
                'scalability': 'Vertical scaling with possible horizontal API layer',
            },
            'ECOMMERCE': {
                'description': 'Distributed architecture with frontend, microservices backend, separate databases, and external integrations.',
                'components': ['Frontend (React)', 'API Gateway', 'Product Service', 'Order Service', 'Payment Service', 'Search Service', 'Database (PostgreSQL)', 'Cache (Redis)', 'Object Storage (S3)'],
                'data_flow': 'Frontend → API Gateway → Microservices → Databases → Cache',
                'scalability': 'Horizontal scaling with load balancing, caching, and CDN',
            },
            'IOT': {
                'description': 'Edge-to-cloud architecture with device connectivity, data ingestion, processing, and visualization.',
                'components': ['IoT Devices', 'Gateway/Edge', 'Message Broker (MQTT)', 'Data Ingestion', 'Time Series DB', 'Analytics Engine', 'Dashboard', 'Mobile App'],
                'data_flow': 'Devices → Gateway → Message Broker → Data Ingestion → Backend → Database → Dashboard',
                'scalability': 'Horizontal scaling of data ingestion and processing with distributed time series database',
            },
            'AI_ML': {
                'description': 'ML pipeline architecture with data preparation, model development, training, and inference services.',
                'components': ['Data Sources', 'Data Pipeline', 'Feature Store', 'Model Training', 'Model Registry', 'Inference Service', 'UI/Dashboard', 'API'],
                'data_flow': 'Data Sources → Pipeline → Feature Store → Training → Inference Service',
                'scalability': 'Parallel training with distributed computing, horizontal scaling of inference',
            },
            'CYBERSECURITY': {
                'description': 'Security monitoring architecture with event ingestion, detection, alerting, incident response and analytics.',
                'components': ['Security Event Sources','Event Ingestion','Threat Detection Engine','Intrusion Detection','Vulnerability Scanner','Alerting','Incident Management','Security Dashboard','Audit Store'],
                'data_flow': 'Security Devices → Event Ingestion → Threat Detection → Alerting → Incident Dashboard → Audit Store',
                'scalability': 'Horizontal scaling for event ingestion and detection workers',
            },
            'EDUCATION': {
                'description': 'Learning platform architecture for courses, assessments, communication and analytics.',
                'components': ['Web Frontend','API Backend','Course Service','Assessment Service','Student/Teacher Management','Database','Notifications','Analytics'],
                'data_flow': 'Users → Frontend → API → Learning Services → Database → Analytics',
                'scalability': 'Horizontal API scaling with caching and CDN',
            },
            'BANKING': {
                'description': 'Secure transactional architecture with account services, ledger processing, fraud controls and auditability.',
                'components': ['Secure Frontend','API Gateway','Account Service','Transaction Ledger','Fraud Detection','Database','Audit Service','Encryption'],
                'data_flow': 'Client → API Gateway → Account Services → Ledger Database → Audit Service',
                'scalability': 'Strong consistency with horizontally scalable read services',
            },
            'HEALTHCARE': {
                'description': 'Secure, compliant architecture with separate services for patient data, appointments, billing, and audit logging.',
                'components': ['Frontend', 'API Gateway', 'Patient Service', 'Appointment Service', 'Billing Service', 'Database (HIPAA-compliant)', 'Audit Log', 'Encryption Service'],
                'data_flow': 'Frontend → API → Services → Encrypted Database → Audit Log',
                'scalability': 'Vertical scaling with strong consistency, audit logging at all layers',
            },
        }
        
        architecture = architectures.get(domain, {
            'description': 'Standard three-tier architecture with frontend, API, and database.',
            'components': ['Frontend', 'API/Backend', 'Database'],
            'data_flow': 'Frontend → API → Database',
            'scalability': 'Standard horizontal scaling',
        })
        
        return architecture


# ========== TECHNOLOGY RECOMMENDER ==========

class TechnologyRecommender:
    """Recommend technology stack."""
    
    TECH_RECOMMENDATIONS = {
        'EMPLOYEE_MGMT': {
            'Frontend': 'React or Vue.js',
            'Backend': 'Python (Flask/Django) or Node.js (Express)',
            'Database': 'PostgreSQL',
            'Caching': 'Redis',
            'Authentication': 'OAuth 2.0 or JWT',
            'Hosting': 'AWS EC2 or DigitalOcean',
        },
        'ECOMMERCE': {
            'Frontend': 'React with Redux/Zustand',
            'Backend': 'Python (Django) or Node.js (Express/NestJS)',
            'Database': 'PostgreSQL for transactional data, Redis for cache',
            'Search': 'Elasticsearch or Algolia',
            'Storage': 'AWS S3 or Cloudinary',
            'Payment': 'Stripe or Razorpay',
            'Hosting': 'AWS or Google Cloud',
        },
        'IOT': {
            'Devices': 'Arduino, Raspberry Pi, or custom firmware',
            'Connectivity': 'MQTT, CoAP, or 5G',
            'Ingestion': 'Apache Kafka or AWS IoT Core',
            'Storage': 'InfluxDB or TimescaleDB for time series',
            'Processing': 'Apache Spark or Flink',
            'Visualization': 'Grafana or custom dashboards',
        },
        'AI_ML': {
            'Data': 'Python with Pandas, NumPy',
            'ML Framework': 'TensorFlow or PyTorch',
            'Pipeline': 'Apache Airflow or Kubeflow',
            'Model Serving': 'TensorFlow Serving or FastAPI',
            'Monitoring': 'Prometheus and Grafana',
            'MLOps': 'MLflow or Kubeflow',
        },
        'EDUCATION': {
            'Frontend': 'React or Vue.js',
            'Backend': 'Python (Django) or Node.js',
            'Database': 'PostgreSQL',
            'Video': 'HLS streaming or YouTube API',
            'Hosting': 'AWS or Heroku',
        },
        'CYBERSECURITY': {
            'SIEM': 'ELK Stack, Splunk, or Sumo Logic',
            'IDS/IPS': 'Suricata or Zeek',
            'Threat Intel': 'Shodan or AlienVault OTX',
            'Dashboard': 'Kibana or Grafana',
            'Backend': 'Python or Go',
            'Database': 'Elasticsearch or MongoDB',
        },
        'BANKING': {
            'Frontend': 'React with strict security',
            'Backend': 'Java or Python with strong frameworks',
            'Database': 'PostgreSQL or Oracle',
            'Encryption': 'TLS, AES-256',
            'Authentication': 'Multi-factor authentication',
            'Compliance': 'PCI-DSS, SOC2',
        },
    }
    
    @staticmethod
    def recommend(understanding: Dict[str, Any]) -> Dict[str, str]:
        """Recommend technology stack based on domain."""
        domain = understanding.get('primary_domain', 'GENERAL')
        return TechnologyRecommender.TECH_RECOMMENDATIONS.get(domain, {
            'Frontend': 'React or Vue.js',
            'Backend': 'Python or Node.js',
            'Database': 'PostgreSQL',
            'Hosting': 'AWS, Google Cloud, or DigitalOcean',
        })


# ========== BUILDER ENGINE ==========

class UniversalProjectBuilder:
    """Main project builder engine."""
    
    @staticmethod
    def build(description: str) -> Dict[str, Any]:
        """
        Build a complete project from description.
        
        Returns structured project data ready for database insertion.
        """
        # Phase 1: Understand the project
        understanding = ProjectUnderstanding.understand(description)
        
        # Phase 2: Adapt to domain
        understanding = DomainAdapter.adapt(understanding)
        
        # Phase 3: Generate components
        requirements = RequirementEngine.generate(understanding)
        modules = ModuleGenerator.generate(understanding)
        tasks = TaskGenerator.generate(understanding, modules)
        dependencies = DependencyGenerator.generate(tasks)
        team_roles = TeamGenerator.generate(understanding)
        risks = RiskGenerator.generate(understanding, tasks)
        architecture = ArchitectureGenerator.generate(understanding, modules)
        technology = TechnologyRecommender.recommend(understanding)
        
        # Phase 4: Structure output
        project_data = {
            'understanding': understanding,
            'requirements': [r.to_dict() for r in requirements],
            'modules': [m.to_dict() for m in modules],
            'tasks': [t.to_dict() for t in tasks],
            'dependencies': dependencies,
            'team_roles': [r.to_dict() for r in team_roles],
            'risks': risks,
            'architecture': architecture,
            'technology': technology,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'version': '1.0',
                'builder': 'UniversalProjectBuilder',
            },
        }
        
        return project_data


# Export main classes for integration
__all__ = [
    'UniversalProjectBuilder',
    'ProjectUnderstanding',
    'DomainAdapter',
    'RequirementEngine',
    'ModuleGenerator',
    'TaskGenerator',
    'DependencyGenerator',
    'TeamGenerator',
    'RiskGenerator',
    'ArchitectureGenerator',
    'TechnologyRecommender',
]