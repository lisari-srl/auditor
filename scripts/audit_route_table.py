import json
import os

def audit_route_table():
    with open("data/route_table_raw.json") as f:
        rt_data = json.load(f)

    route_tables = rt_data.get("RouteTables", [])
    os.makedirs("data", exist_ok=True)
    with open("data/route_table_audit.json", "w") as f:
        json.dump({"route_tables": route_tables}, f, indent=2)

    os.makedirs("reports", exist_ok=True)
    with open("reports/audit_route_table_report.md", "w") as report:
        report.write("# Route Table Audit Report\n\n")
        for rt in rt_data["RouteTables"]:
            # logica di audit
            report.write(f"- {rt.get('RouteTableId')} | VPC: {rt.get('VpcId')}\n")
            for route in rt.get("Routes", []):
                # logica sulle rotte
                report.write(f"  - {route.get('DestinationCidrBlock')} -> {route.get('GatewayId')}\n")
    print("✅ Route Table audit completato e salvato in /data e /reports")

if __name__ == "__main__":
    audit_route_table()