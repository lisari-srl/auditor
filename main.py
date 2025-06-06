# Enhanced main.py - Integrazione con Cost Analysis e Optimization

# Aggiungi queste import in cima al file main.py esistente:
from utils.cost_analysis_fetcher import CostAnalysisFetcher
from utils.infrastructure_optimizer import InfrastructureOptimizer
from audit.advanced_sg_auditor import AdvancedSecurityGroupAuditor

# Aggiungi questa nuova classe per orchestrare il tutto:
class EnhancedAWSAuditor(AWSAuditor):
    """Versione avanzata dell'auditor con analisi costi e ottimizzazione"""
    
    def __init__(self, config_file: Optional[str] = None):
        super().__init__(config_file)
        self.cost_fetcher = CostAnalysisFetcher(self.config)
        self.optimizer = None
        
    async def run_enhanced_audit(self, include_cost_analysis: bool = True, 
                                 generate_optimization_plan: bool = True) -> dict:
        """Esegue audit completo con analisi costi e piano di ottimizzazione"""
        print("🚀 Avvio Enhanced AWS Security & Cost Audit...")
        start_time = time.time()
        
        try:
            # 1. Audit di sicurezza standard
            print("\n🔍 FASE 1: Security Audit...")
            security_result = await self.run_full_audit(use_cache=True, force_cleanup=False)
            
            # 2. Analisi costi se richiesta
            cost_data = {}
            if include_cost_analysis:
                print("\n💰 FASE 2: Cost Analysis...")
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                cost_data = await self.cost_fetcher.fetch_cost_data(start_date, end_date)
                
                # Fetch risorse aggiuntive per analisi completa
                additional_resources = await self.cost_fetcher.fetch_additional_resources()
                
                # Salva dati di costo
                os.makedirs("data", exist_ok=True)
                with open("data/cost_analysis.json", "w") as f:
                    json.dump(cost_data, f, indent=2, default=str)
                
                with open("data/additional_resources.json", "w") as f:
                    json.dump(additional_resources, f, indent=2, default=str)
                
                print(f"   ✅ Cost analysis completato")
            
            # 3. Audit avanzato Security Groups
            print("\n🛡️  FASE 3: Advanced Security Groups Analysis...")
            await self._run_advanced_sg_audit()
            
            # 4. Generazione piano di ottimizzazione
            optimization_result = {}
            if generate_optimization_plan:
                print("\n⚡ FASE 4: Optimization Planning...")
                optimization_result = await self._generate_optimization_plan(cost_data)
            
            total_time = time.time() - start_time
            
            # 5. Report finale enhanced
            final_result = {
                **security_result,
                "cost_analysis": {
                    "enabled": include_cost_analysis,
                    "current_monthly_cost": optimization_result.get("current_monthly_cost", 0),
                    "potential_monthly_savings": optimization_result.get("potential_monthly_savings", 0),
                    "cost_data_available": bool(cost_data)
                },
                "optimization": {
                    "enabled": generate_optimization_plan,
                    "total_recommendations": optimization_result.get("total_recommendations", 0),
                    "quick_wins": len(optimization_result.get("quick_wins", [])),
                    "high_impact_changes": len(optimization_result.get("high_impact_changes", []))
                },
                "enhanced_audit_time": total_time
            }
            
            # 6. Print enhanced summary
            self._print_enhanced_summary(final_result, optimization_result)
            
            # 7. Generate enhanced reports
            if generate_optimization_plan and optimization_result:
                self._generate_enhanced_reports(optimization_result)
            
            return final_result
            
        except Exception as e:
            print(f"\n❌ Enhanced audit failed: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def _run_advanced_sg_audit(self):
        """Esegue audit avanzato dei Security Groups"""
        try:
            # Carica dati necessari
            sg_data = self._load_json_data("data/sg_raw.json")
            eni_data = self._load_json_data("data/eni_raw.json")
            ec2_data = self._load_json_data("data/ec2_raw.json")
            
            if not sg_data:
                print("   ⚠️  No Security Groups data available for advanced analysis")
                return
            
            # Combina dati per l'audit avanzato
            combined_data = {
                "SecurityGroups": sg_data.get("SecurityGroups", []),
                "NetworkInterfaces": eni_data.get("NetworkInterfaces", []),
                "ec2_raw": ec2_data
            }
            
            # Esegui audit avanzato
            advanced_auditor = AdvancedSecurityGroupAuditor(region=self.config.regions[0])
            findings = advanced_auditor.audit(combined_data)
            
            # Salva risultati avanzati
            optimization_summary = advanced_auditor.get_optimization_summary()
            
            with open("data/advanced_sg_analysis.json", "w") as f:
                json.dump({
                    "findings": [f.to_dict() for f in findings],
                    "optimization_summary": optimization_summary,
                    "analysis_timestamp": datetime.now().isoformat()
                }, f, indent=2)
            
            # Genera script di cleanup
            cleanup_script = advanced_auditor.generate_cleanup_script({})
            with open("scripts/sg_cleanup.sh", "w") as f:
                f.write(cleanup_script)
            os.chmod("scripts/sg_cleanup.sh", 0o755)
            
            print(f"   ✅ Advanced SG analysis: {len(findings)} detailed findings")
            print(f"   📋 Optimization recommendations: {optimization_summary['total_recommendations']}")
            print(f"   💰 Cost savings opportunities: {optimization_summary['cost_savings_opportunities']}")
            
        except Exception as e:
            print(f"   ❌ Advanced SG audit failed: {e}")
    
    async def _generate_optimization_plan(self, cost_data: Dict) -> Dict:
        """Genera piano di ottimizzazione completo"""
        try:
            # Carica tutti i dati di audit
            audit_data = {
                "ec2_audit": self._load_json_data("data/ec2_audit.json"),
                "sg_audit": self._load_json_data("data/sg_audit.json"),
                "s3_audit": self._load_json_data("data/s3_audit.json"),
                "iam_audit": self._load_json_data("data/iam_audit.json"),
                "vpc_audit": self._load_json_data("data/vpc_audit.json"),
                "ebs": self._load_json_data("data/additional_resources.json", {}).get("ebs", {}),
                "load_balancers": self._load_json_data("data/additional_resources.json", {}).get("load_balancers", {})
            }
            
            # Inizializza optimizer
            self.optimizer = InfrastructureOptimizer(audit_data, cost_data)
            
            # Genera piano di ottimizzazione
            optimization_result = self.optimizer.analyze_and_optimize()
            
            # Salva risultati
            with open("reports/optimization_plan.json", "w") as f:
                json.dump(optimization_result, f, indent=2)
            
            # Genera script di cleanup
            cleanup_script = self.optimizer.generate_cleanup_script()
            os.makedirs("scripts", exist_ok=True)
            with open("scripts/infrastructure_cleanup.sh", "w") as f:
                f.write(cleanup_script)
            os.chmod("scripts/infrastructure_cleanup.sh", 0o755)
            
            # Genera cost report
            cost_report = self.optimizer.generate_cost_report()
            with open("reports/cost_optimization_report.md", "w") as f:
                f.write(cost_report)
            
            print(f"   ✅ Optimization plan generated")
            print(f"   💰 Current monthly cost: ${optimization_result['current_monthly_cost']:.2f}")
            print(f"   💵 Potential savings: ${optimization_result['potential_monthly_savings']:.2f}/month")
            print(f"   📋 Total recommendations: {optimization_result['total_recommendations']}")
            
            return optimization_result
            
        except Exception as e:
            print(f"   ❌ Optimization planning failed: {e}")
            return {}
    
    def _print_enhanced_summary(self, final_result: Dict, optimization_result: Dict):
        """Print summary enhanced con costi e ottimizzazioni"""
        print(f"\n🎯 ENHANCED AUDIT SUMMARY")
        print("=" * 60)
        
        # Security summary
        print(f"🔒 SECURITY:")
        print(f"   Total Findings: {final_result.get('total_findings', 0)}")
        print(f"   🔴 Critical: {final_result.get('critical_findings', 0)}")
        print(f"   🟠 High: {final_result.get('high_findings', 0)}")
        
        # Cost summary
        if final_result["cost_analysis"]["enabled"]:
            print(f"\n💰 COST ANALYSIS:")
            print(f"   Current Monthly Cost: ${final_result['cost_analysis']['current_monthly_cost']:.2f}")
            print(f"   Potential Monthly Savings: ${final_result['cost_analysis']['potential_monthly_savings']:.2f}")
            if final_result['cost_analysis']['potential_monthly_savings'] > 0:
                annual_savings = final_result['cost_analysis']['potential_monthly_savings'] * 12
                print(f"   Potential Annual Savings: ${annual_savings:.2f}")
        
        # Optimization summary
        if final_result["optimization"]["enabled"]:
            print(f"\n⚡ OPTIMIZATION:")
            print(f"   Total Recommendations: {final_result['optimization']['total_recommendations']}")
            print(f"   Quick Wins: {final_result['optimization']['quick_wins']}")
            print(f"   High Impact Changes: {final_result['optimization']['high_impact_changes']}")
        
        print(f"\n⏱️  Total Enhanced Audit Time: {final_result['enhanced_audit_time']:.2f}s")
        print("=" * 60)
        
        # Next steps
        print(f"\n💡 NEXT STEPS:")
        print(f"   📊 Enhanced Dashboard: python main.py --enhanced-dashboard")
        print(f"   🔧 Run Cleanup: ./scripts/infrastructure_cleanup.sh")
        print(f"   📋 Cost Report: cat reports/cost_optimization_report.md")
        print(f"   🛡️  SG Cleanup: ./scripts/sg_cleanup.sh")
    
    def _generate_enhanced_reports(self, optimization_result: Dict):
        """Genera report enhanced"""
        # Executive Summary Report
        executive_summary = self._generate_executive_summary(optimization_result)
        with open("reports/executive_summary.md", "w") as f:
            f.write(executive_summary)
        
        # Technical Implementation Guide
        tech_guide = self._generate_technical_guide(optimization_result)
        with open("reports/technical_implementation_guide.md", "w") as f:
            f.write(tech_guide)
        
        print(f"   📄 Enhanced reports generated in /reports")
    
    def _generate_executive_summary(self, optimization_result: Dict) -> str:
        """Genera executive summary per management"""
        quick_wins = optimization_result.get("quick_wins", [])
        immediate_savings = optimization_result.get("implementation_plan", {}).get("immediate_savings", 0)
        
        return f"""# 📊 AWS Infrastructure Executive Summary

## Current State
- **Monthly Infrastructure Cost**: ${optimization_result['current_monthly_cost']:.2f}
- **Security Issues Found**: {len([r for r in optimization_result.get('detailed_recommendations', []) if r['optimization_type'] == 'security_improvement'])}
- **Unused Resources**: {len([r for r in optimization_result.get('detailed_recommendations', []) if r['optimization_type'] == 'cleanup'])}

## Optimization Opportunity
- **Potential Monthly Savings**: ${optimization_result['potential_monthly_savings']:.2f}
- **Potential Annual Savings**: ${optimization_result['potential_monthly_savings'] * 12:.2f}
- **ROI Timeline**: 1-3 months

## Quick Wins (Immediate Actions)
These changes can be implemented this week with minimal risk:
"""+ "\n".join([f"- {qw['title']} - ${qw['savings']:.2f}/month" for qw in quick_wins]) + f"""

## Security Priority
- **Critical Issues**: Immediate attention required
- **Compliance**: CIS, SOC2, PCI-DSS improvements available
- **Risk Reduction**: Significant security posture improvement possible

## Recommended Timeline
- **Week 1**: Critical security fixes and quick wins (${immediate_savings:.2f}/month savings)
- **Month 1**: Complete security optimization
- **Month 2-3**: Full cost optimization implementation

*Generated by AWS Security Auditor on {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    
    def _generate_technical_guide(self, optimization_result: Dict) -> str:
        """Genera guida tecnica per implementazione"""
        return f"""# 🔧 Technical Implementation Guide

## Prerequisites
- AWS CLI configured with appropriate permissions
- Backup procedures in place
- Change management approval for critical resources

## Phase 1: Immediate Security Fixes
```bash
# Critical Security Group fixes
./scripts/sg_cleanup.sh

# IAM cleanup
./scripts/iam_cleanup.sh
```

## Phase 2: Cost Optimization
```bash
# Infrastructure cleanup
./scripts/infrastructure_cleanup.sh

# Monitoring setup for ongoing optimization
aws cloudwatch put-metric-alarm --alarm-name "HighCostAlert" ...
```

## Phase 3: Ongoing Monitoring
- Setup cost budgets and alerts
- Implement automated resource cleanup
- Regular security audits

## Rollback Procedures
Each script generates corresponding rollback procedures in `/scripts/rollback/`

## Monitoring
- Use enhanced dashboard: `python main.py --enhanced-dashboard`
- Set up weekly automated audits: `crontab -e`

*For questions, consult the detailed recommendations in optimization_plan.json*
"""
    
    def _load_json_data(self, file_path: str, default=None) -> Dict:
        """Carica dati JSON con fallback"""
        if default is None:
            default = {}
        try:
            if os.path.exists(file_path):
                with open(file_path) as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading {file_path}: {e}")
        return default
    
    def start_enhanced_dashboard(self, host: str = "localhost"):
        """Avvia dashboard enhanced con dati di costo e ottimizzazione"""
        print("🚀 Avvio Enhanced Dashboard con Cost Analysis...")
        
        # Verifica che esistano dati enhanced
        enhanced_files = [
            "data/cost_analysis.json",
            "data/additional_resources.json", 
            "reports/optimization_plan.json"
        ]
        
        missing_files = [f for f in enhanced_files if not os.path.exists(f)]
        if missing_files:
            print("⚠️ Some enhanced data missing. Run enhanced audit first:")
            print("   python main.py --enhanced-audit")
            for f in missing_files:
                print(f"   Missing: {f}")
        
        # Lancia dashboard normale (che ora include dati enhanced se disponibili)
        self.start_dashboard(host)

# Modifica la funzione main() esistente per includere opzioni enhanced:
def enhanced_main():
    """Enhanced main function con opzioni per cost analysis"""
    parser = argparse.ArgumentParser(
        description="🔍 AWS Infrastructure Security & Cost Auditor v2.1 Enhanced",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Enhanced Examples:
  python main.py --enhanced-audit              # Full security + cost + optimization
  python main.py --enhanced-audit --no-cost   # Security + optimization only  
  python main.py --cost-analysis-only         # Only cost analysis
  python main.py --enhanced-dashboard         # Dashboard with cost data
  python main.py --optimization-plan          # Generate optimization plan from existing data
        """
    )
    
    # Aggiungi opzioni enhanced al parser esistente
    parser.add_argument(
        "--enhanced-audit",
        action="store_true",
        help="Run enhanced audit with cost analysis and optimization planning"
    )
    parser.add_argument(
        "--cost-analysis-only", 
        action="store_true",
        help="Run only cost analysis"
    )
    parser.add_argument(
        "--optimization-plan",
        action="store_true",
        help="Generate optimization plan from existing audit data"
    )
    parser.add_argument(
        "--enhanced-dashboard",
        action="store_true",
        help="Start enhanced dashboard with cost and optimization data"
    )
    parser.add_argument(
        "--no-cost",
        action="store_true", 
        help="Skip cost analysis in enhanced audit"
    )
    
    args = parser.parse_args()
    
    try:
        # Crea enhanced auditor
        auditor = EnhancedAWSAuditor(args.config)
        
        # Override configurazione da CLI se specificato
        if args.regions:
            auditor.config.regions = [r.strip() for r in args.regions.split(",")]
        
        # Esegui operazione richiesta
        if args.enhanced_audit:
            include_cost = not args.no_cost
            result = asyncio.run(auditor.run_enhanced_audit(
                include_cost_analysis=include_cost,
                generate_optimization_plan=True
            ))
            sys.exit(0 if result.get("success", True) else 1)
            
        elif args.cost_analysis_only:
            print("💰 Running cost analysis only...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            cost_data = asyncio.run(auditor.cost_fetcher.fetch_cost_data(start_date, end_date))
            
            with open("data/cost_analysis.json", "w") as f:
                json.dump(cost_data, f, indent=2, default=str)
            print("✅ Cost analysis completed: data/cost_analysis.json")
            
        elif args.optimization_plan:
            print("⚡ Generating optimization plan from existing data...")
            cost_data = auditor._load_json_data("data/cost_analysis.json")
            result = asyncio.run(auditor._generate_optimization_plan(cost_data))
            print("✅ Optimization plan generated: reports/optimization_plan.json")
            
        elif args.enhanced_dashboard:
            auditor.start_enhanced_dashboard(host=args.host)
            
        else:
            # Fallback to original main function for backwards compatibility
            main()
            
    except KeyboardInterrupt:
        print("\n🛑 Operazione interrotta dall'utente")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Errore enhanced audit: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    enhanced_main()