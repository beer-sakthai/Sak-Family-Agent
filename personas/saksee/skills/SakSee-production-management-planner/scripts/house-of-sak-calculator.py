#!/usr/bin/env python3
"""
House of Sak Service Metrics Calculator

A script to calculate key service delivery metrics including costs, efficiency, and performance indicators 
specifically for QA automation, AI dataset publishing, and API prototyping services.
"""

def calculate_production_cost(material_cost, labor_cost, equipment_cost, overhead_cost):
    """Calculate total production cost"""
    return material_cost + labor_cost + equipment_cost + overhead_cost

def calculate_efficiency(actual_output, standard_output):
    """Calculate production efficiency percentage"""
    if standard_output == 0:
        return 0
    return (actual_output / standard_output) * 100

def calculate_resource_utilization(used_time, available_time):
    """Calculate resource utilization percentage"""
    if available_time == 0:
        return 0
    return (used_time / available_time) * 100

def calculate_throughput(total_units, total_time):
    """Calculate throughput (units per time period)"""
    if total_time == 0:
        return 0
    return total_units / total_time

def calculate_oee(availability, performance, quality):
    """Calculate Overall Equipment Effectiveness (OEE)"""
    return (availability / 100) * (performance / 100) * (quality / 100) * 100

def calculate_qa_metrics(tests_planned, tests_executed, tests_passed, execution_time):
    """Calculate QA automation specific metrics"""
    if tests_planned == 0:
        test_coverage = 0
    else:
        test_coverage = (tests_executed / tests_planned) * 100
    
    if tests_executed == 0:
        pass_rate = 0
    else:
        pass_rate = (tests_passed / tests_executed) * 100
    
    return {
        'test_coverage': test_coverage,
        'pass_rate': pass_rate,
        'execution_time': execution_time
    }

def calculate_dataset_metrics(records_processed, quality_score, processing_time):
    """Calculate AI dataset publishing specific metrics"""
    return {
        'records_processed': records_processed,
        'quality_score': quality_score,
        'processing_time': processing_time,
        'throughput': records_processed / processing_time if processing_time > 0 else 0
    }

def calculate_api_metrics(endpoints_built, response_time_avg, uptime_percentage):
    """Calculate API prototyping specific metrics"""
    return {
        'endpoints_built': endpoints_built,
        'avg_response_time': response_time_avg,
        'uptime_percentage': uptime_percentage
    }

def generate_service_report(project_name, service_type, metrics):
    """Generate a formatted service delivery report"""
    report = f"""
HOUSE OF SAK SERVICE REPORT: {project_name}
{'=' * (25 + len(project_name))}

SERVICE TYPE: {service_type}

SUMMARY METRICS:
- Total Service Cost: ${metrics.get('total_cost', 0):,.2f}
- Service Efficiency: {metrics.get('efficiency', 0):.2f}%
- Resource Utilization: {metrics.get('utilization', 0):.2f}%
- Service Delivery Time: {metrics.get('delivery_time', 0):.2f} hours
- Quality Score: {metrics.get('quality_score', 0):.2f}%

COST BREAKDOWN:
- Material Costs: ${metrics.get('material_cost', 0):,.2f}
- Labor Costs: ${metrics.get('labor_cost', 0):,.2f}
- Equipment Costs: ${metrics.get('equipment_cost', 0):,.2f}
- Overhead Costs: ${metrics.get('overhead_cost', 0):,.2f}

PERFORMANCE INDICATORS:
- On-time Delivery: {metrics.get('on_time_delivery', 0):.2f}%
- Client Satisfaction: {metrics.get('client_satisfaction', 0):.2f}%
- Cost Variance: {metrics.get('cost_variance', 0):.2f}%
"""
    
    # Add service-specific metrics
    if service_type == "QA Automation":
        report += f"""
QA SPECIFIC METRICS:
- Test Coverage: {metrics.get('test_coverage', 0):.2f}%
- Pass Rate: {metrics.get('pass_rate', 0):.2f}%
- Execution Time: {metrics.get('execution_time', 0):.2f} seconds
"""
    elif service_type == "AI Dataset Publishing":
        report += f"""
DATASET SPECIFIC METRICS:
- Records Processed: {metrics.get('records_processed', 0):,}
- Data Quality Score: {metrics.get('quality_score', 0):.2f}%
- Processing Throughput: {metrics.get('throughput', 0):,.2f} records/hour
"""
    elif service_type == "API Prototyping":
        report += f"""
API SPECIFIC METRICS:
- Endpoints Built: {metrics.get('endpoints_built', 0)}
- Avg Response Time: {metrics.get('avg_response_time', 0):.2f} ms
- Uptime: {metrics.get('uptime_percentage', 0):.2f}%
"""
    
    return report

def calculate_pricing_for_service(service_type, complexity_factor=1.0):
    """Calculate recommended pricing based on service type and complexity"""
    base_prices = {
        "QA Automation": {"min": 200, "max": 500},
        "AI Dataset Publishing": {"min": 300, "max": 800},
        "API Prototyping": {"min": 150, "max": 400}
    }
    
    if service_type in base_prices:
        base_min = base_prices[service_type]["min"]
        base_max = base_prices[service_type]["max"]
        return {
            "min_price": base_min * complexity_factor,
            "max_price": base_max * complexity_factor
        }
    else:
        return {"min_price": 0, "max_price": 0}

if __name__ == "__main__":
    # Example usage
    print("House of Sak Service Metrics Calculator")
    print("-" * 40)
    
    # Sample calculations for QA Automation
    total_cost = calculate_production_cost(0, 0, 20, 0)  # Only equipment costs
    efficiency = calculate_efficiency(10, 10)  # 10 out of 10 tests executed
    utilization = calculate_resource_utilization(40, 48)  # 40 out of 48 hours used
    qa_metrics = calculate_qa_metrics(25, 25, 23, 120)  # 25 tests, 23 passed, 120 seconds
    
    metrics = {
        'total_cost': total_cost,
        'efficiency': efficiency,
        'utilization': utilization,
        'delivery_time': 3,
        'quality_score': 92.0,
        'material_cost': 0,
        'labor_cost': 0,
        'equipment_cost': 20,
        'overhead_cost': 0,
        'on_time_delivery': 100.0,
        'client_satisfaction': 95.0,
        'cost_variance': -5.0,
        'test_coverage': qa_metrics['test_coverage'],
        'pass_rate': qa_metrics['pass_rate'],
        'execution_time': qa_metrics['execution_time']
    }
    
    report = generate_service_report("Sample QA Project", "QA Automation", metrics)
    print(report)
    
    # Pricing calculation
    pricing = calculate_pricing_for_service("QA Automation", 1.2)
    print(f"RECOMMENDED PRICING: €{pricing['min_price']:.0f} - €{pricing['max_price']:.0f}")