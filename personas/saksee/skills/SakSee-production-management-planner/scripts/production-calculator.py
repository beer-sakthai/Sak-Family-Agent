#!/usr/bin/env python3
"""
Production Metrics Calculator

A script to calculate key production metrics including costs, efficiency, and performance indicators.
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

def calculate_oeep(availability, performance, quality):
    """Calculate Overall Equipment Effectiveness (OEE)"""
    return (availability / 100) * (performance / 100) * (quality / 100) * 100

def generate_production_report(project_name, metrics):
    """Generate a formatted production report"""
    report = f"""
PRODUCTION REPORT: {project_name}
{'=' * (20 + len(project_name))}

SUMMARY METRICS:
- Total Production Cost: ${metrics.get('total_cost', 0):,.2f}
- Production Efficiency: {metrics.get('efficiency', 0):.2f}%
- Resource Utilization: {metrics.get('utilization', 0):.2f}%
- Throughput: {metrics.get('throughput', 0):.2f} units/hour
- Overall Equipment Effectiveness: {metrics.get('oee', 0):.2f}%

COST BREAKDOWN:
- Material Costs: ${metrics.get('material_cost', 0):,.2f}
- Labor Costs: ${metrics.get('labor_cost', 0):,.2f}
- Equipment Costs: ${metrics.get('equipment_cost', 0):,.2f}
- Overhead Costs: ${metrics.get('overhead_cost', 0):,.2f}

PERFORMANCE INDICATORS:
- Quality Rate: {metrics.get('quality_rate', 0):.2f}%
- On-time Delivery: {metrics.get('on_time_delivery', 0):.2f}%
- Cost Variance: {metrics.get('cost_variance', 0):.2f}%
"""
    return report

if __name__ == "__main__":
    # Example usage
    print("Production Metrics Calculator")
    print("-" * 30)
    
    # Sample calculations
    total_cost = calculate_production_cost(10000, 5000, 2000, 1500)
    efficiency = calculate_efficiency(950, 1000)
    utilization = calculate_resource_utilization(40, 48)
    throughput = calculate_throughput(1000, 8)
    oee = calculate_oeep(95, 90, 98)
    
    metrics = {
        'total_cost': total_cost,
        'efficiency': efficiency,
        'utilization': utilization,
        'throughput': throughput,
        'oee': oee,
        'material_cost': 10000,
        'labor_cost': 5000,
        'equipment_cost': 2000,
        'overhead_cost': 1500,
        'quality_rate': 98.5,
        'on_time_delivery': 95.0,
        'cost_variance': -2.5
    }
    
    report = generate_production_report("Sample Project", metrics)
    print(report)