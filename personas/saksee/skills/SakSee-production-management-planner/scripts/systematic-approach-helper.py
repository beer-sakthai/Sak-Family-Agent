#!/usr/bin/env python3
"""
Systematic Approach Implementation Helper

A script to guide the implementation of the 4-phase systematic approach
for House of Sak service delivery.
"""

def plan_phase_checklist(service_type):
    """Generate a checklist for the Plan phase based on service type"""
    checklists = {
        "QA Automation": [
            "Define test scenarios and user flows",
            "Identify critical paths to test",
            "Set up test environment access",
            "Create detailed test plan document",
            "Establish success criteria and KPIs",
            "Document client requirements and expectations"
        ],
        "AI Agent Development": [
            "Analyze client data and documentation",
            "Define use cases and capabilities",
            "Create training data plan",
            "Set up development environment",
            "Establish performance benchmarks",
            "Document integration requirements"
        ],
        "Web Prototyping": [
            "Gather detailed requirements",
            "Create wireframes and mockups",
            "Define functionality and features",
            "Select appropriate technologies",
            "Establish design guidelines",
            "Document hosting and deployment requirements"
        ],
        "System Auditing": [
            "Define audit scope and objectives",
            "Identify critical systems to examine",
            "Gather access credentials and documentation",
            "Establish severity rating criteria",
            "Set up analysis tools and frameworks",
            "Document reporting requirements"
        ]
    }
    
    return checklists.get(service_type, ["Define project scope and objectives"])

def execute_phase_checklist(service_type):
    """Generate a checklist for the Execute phase based on service type"""
    checklists = {
        "QA Automation": [
            "Set up Playwright testing environment",
            "Implement cross-browser test coverage",
            "Create test data and scenarios",
            "Integrate with CI/CD pipeline",
            "Run initial test suite",
            "Document test execution process"
        ],
        "AI Agent Development": [
            "Build initial agent prototype",
            "Train agent on client data",
            "Implement fallback mechanisms",
            "Set up deployment infrastructure",
            "Test agent responses and accuracy",
            "Document training and configuration"
        ],
        "Web Prototyping": [
            "Set up development environment",
            "Implement core functionality",
            "Create responsive design",
            "Integrate required APIs and services",
            "Test across different devices/browsers",
            "Document development process and decisions"
        ],
        "System Auditing": [
            "Perform code quality analysis",
            "Check security vulnerabilities",
            "Assess performance metrics",
            "Review reliability factors",
            "Document findings with evidence",
            "Prioritize issues by severity"
        ]
    }
    
    return checklists.get(service_type, ["Implement service delivery plan"])

def measure_phase_checklist(service_type):
    """Generate a checklist for the Measure phase based on service type"""
    checklists = {
        "QA Automation": [
            "Run complete test suite execution",
            "Capture bug reports with screenshots",
            "Generate test coverage metrics",
            "Measure execution time and performance",
            "Track pass/fail rates",
            "Document results and findings"
        ],
        "AI Agent Development": [
            "Test agent with real queries",
            "Measure response accuracy rates",
            "Track conversation success metrics",
            "Monitor resource utilization",
            "Generate performance benchmarks",
            "Document testing results"
        ],
        "Web Prototyping": [
            "Test across multiple devices/browsers",
            "Measure page load performance",
            "Check accessibility compliance",
            "Validate functionality against requirements",
            "Generate performance metrics",
            "Document testing outcomes"
        ],
        "System Auditing": [
            "Rank findings by severity level",
            "Generate detailed metrics report",
            "Create visualizations of key data",
            "Track issue resolution progress",
            "Measure overall system health",
            "Document measurement methodology"
        ]
    }
    
    return checklists.get(service_type, ["Track performance against KPIs"])

def improve_phase_checklist(service_type):
    """Generate a checklist for the Improve phase based on service type"""
    checklists = {
        "QA Automation": [
            "Analyze test failure patterns",
            "Identify areas for test optimization",
            "Update test maintenance procedures",
            "Document lessons learned",
            "Refine test scenarios and coverage",
            "Update templates and best practices"
        ],
        "AI Agent Development": [
            "Analyze agent performance gaps",
            "Identify training data improvements",
            "Refine response handling logic",
            "Document optimization strategies",
            "Update agent capabilities",
            "Create improvement roadmap"
        ],
        "Web Prototyping": [
            "Analyze user feedback and testing results",
            "Identify design and functionality improvements",
            "Optimize performance and loading times",
            "Document best practices and lessons learned",
            "Refine development processes",
            "Update template and component library"
        ],
        "System Auditing": [
            "Analyze recurring issue patterns",
            "Identify systemic improvement opportunities",
            "Document resolution recommendations",
            "Track improvement implementation",
            "Refine audit criteria and methods",
            "Update best practices and guidelines"
        ]
    }
    
    return checklists.get(service_type, ["Analyze outcomes and document improvements"])

def github_workflow_checklist():
    """Generate a checklist for GitHub workflow best practices"""
    return [
        "Commit changes with clear, descriptive messages",
        "Create patch files when direct push fails: git format-patch HEAD~1..HEAD",
        "Generate README documentation for patch files",
        "Test changes locally before creating patches",
        "Maintain consistent branch naming conventions",
        "Use feature branches for significant changes",
        "Document any authentication issues and workarounds"
    ]

def generate_systematic_approach_guide(service_type):
    """Generate a complete guide for implementing the systematic approach"""
    guide = f"""
HOUSE OF SAK SYSTEMATIC APPROACH GUIDE
Service Type: {service_type}
====================================

PHASE 1: PLAN
-------------
Checklist:
"""
    for item in plan_phase_checklist(service_type):
        guide += f"- [ ] {item}\n"
    
    guide += f"""
PHASE 2: EXECUTE
----------------
Checklist:
"""
    for item in execute_phase_checklist(service_type):
        guide += f"- [ ] {item}\n"
    
    guide += f"""
PHASE 3: MEASURE
----------------
Checklist:
"""
    for item in measure_phase_checklist(service_type):
        guide += f"- [ ] {item}\n"
    
    guide += f"""
PHASE 4: IMPROVE
----------------
Checklist:
"""
    for item in improve_phase_checklist(service_type):
        guide += f"- [ ] {item}\n"
    
    guide += f"""
GITHUB WORKFLOW BEST PRACTICES
------------------------------
Checklist:
"""
    for item in github_workflow_checklist():
        guide += f"- [ ] {item}\n"
    
    return guide

if __name__ == "__main__":
    # Example usage
    print("House of Sak Systematic Approach Implementation Helper")
    print("=" * 55)
    
    # Generate guide for QA Automation as an example
    guide = generate_systematic_approach_guide("QA Automation")
    print(guide)
    
    print("\n" + "=" * 55)
    print("To generate a guide for a different service type, call:")
    print("generate_systematic_approach_guide('Service Type')")