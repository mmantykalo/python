#!/usr/bin/env python3
"""
Production monitoring script for geosocial API
Checks health, performance metrics, and alerts on issues
"""

import json
import time
import sys
import subprocess
import requests
from datetime import datetime
from pathlib import Path

class ProductionMonitor:
    def __init__(self):
        self.health_url = "http://localhost:8000/health"
        self.api_url = "http://localhost:8000/api/v1"
        self.log_file = Path("./logs/monitoring.log")
        self.alert_thresholds = {
            'response_time': 2.0,  # seconds
            'memory_usage': 80,    # percentage
            'cpu_usage': 80,       # percentage
            'disk_usage': 85       # percentage
        }
    
    def log_message(self, level: str, message: str):
        """Log message with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        # Write to log file
        self.log_file.parent.mkdir(exist_ok=True, parents=True)
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
    
    def check_health(self) -> dict:
        """Check application health endpoint"""
        try:
            start_time = time.time()
            response = requests.get(self.health_url, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                return {
                    'status': 'healthy',
                    'response_time': response_time,
                    'data': health_data
                }
            else:
                return {
                    'status': 'unhealthy',
                    'response_time': response_time,
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_containers(self) -> dict:
        """Check Docker container status and resource usage"""
        try:
            # Get container status
            result = subprocess.run([
                'docker', 'compose', '-f', 'docker-compose.prod.yml', 'ps', '--format', 'json'
            ], capture_output=True, text=True, check=True)
            
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    container = json.loads(line)
                    containers.append(container)
            
            # Get resource usage
            stats_result = subprocess.run([
                'docker', 'stats', '--no-stream', '--format', 
                'table {{.Container}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}}'
            ], capture_output=True, text=True, check=True)
            
            return {
                'status': 'ok',
                'containers': containers,
                'stats': stats_result.stdout
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_database(self) -> dict:
        """Check database connectivity through API"""
        try:
            # This assumes you have a database status endpoint
            response = requests.get(f"{self.api_url}/status", timeout=5)
            if response.status_code == 200:
                return {'status': 'connected'}
            else:
                return {'status': 'error', 'code': response.status_code}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def check_disk_usage(self) -> dict:
        """Check disk usage for Docker volumes"""
        try:
            result = subprocess.run(['df', '-h'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            disk_info = []
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 6:
                        usage_percent = int(parts[4].rstrip('%'))
                        disk_info.append({
                            'filesystem': parts[0],
                            'size': parts[1],
                            'used': parts[2],
                            'available': parts[3],
                            'usage_percent': usage_percent,
                            'mountpoint': parts[5]
                        })
            
            return {'status': 'ok', 'disks': disk_info}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def analyze_logs(self) -> dict:
        """Analyze recent logs for errors"""
        try:
            log_file = Path('./logs/app.log')
            if not log_file.exists():
                return {'status': 'no_logs', 'message': 'Log file not found'}
            
            # Read last 100 lines
            result = subprocess.run(['tail', '-100', str(log_file)], 
                                  capture_output=True, text=True)
            
            lines = result.stdout.split('\n')
            errors = [line for line in lines if 'ERROR' in line]
            warnings = [line for line in lines if 'WARNING' in line or 'WARN' in line]
            
            return {
                'status': 'analyzed',
                'total_lines': len(lines),
                'errors': len(errors),
                'warnings': len(warnings),
                'recent_errors': errors[-5:] if errors else [],
                'recent_warnings': warnings[-5:] if warnings else []
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def run_full_check(self) -> dict:
        """Run all monitoring checks"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'health': self.check_health(),
            'containers': self.check_containers(),
            'database': self.check_database(),
            'disk': self.check_disk_usage(),
            'logs': self.analyze_logs()
        }
        
        # Determine overall status
        critical_issues = []
        warnings = []
        
        # Check health
        if results['health']['status'] != 'healthy':
            critical_issues.append("Application health check failed")
        elif results['health'].get('response_time', 0) > self.alert_thresholds['response_time']:
            warnings.append(f"Slow response time: {results['health']['response_time']:.2f}s")
        
        # Check containers
        if results['containers']['status'] != 'ok':
            critical_issues.append("Container check failed")
        
        # Check database
        if results['database']['status'] != 'connected':
            critical_issues.append("Database connectivity issues")
        
        # Check disk usage
        if results['disk']['status'] == 'ok':
            for disk in results['disk']['disks']:
                if disk['usage_percent'] > self.alert_thresholds['disk_usage']:
                    critical_issues.append(f"High disk usage: {disk['usage_percent']}% on {disk['filesystem']}")
        
        # Check logs
        if results['logs']['status'] == 'analyzed' and results['logs']['errors'] > 0:
            warnings.append(f"Found {results['logs']['errors']} recent errors in logs")
        
        results['overall_status'] = {
            'status': 'critical' if critical_issues else ('warning' if warnings else 'healthy'),
            'critical_issues': critical_issues,
            'warnings': warnings
        }
        
        return results
    
    def print_summary(self, results: dict):
        """Print monitoring summary"""
        status = results['overall_status']['status']
        print(f"\n{'='*60}")
        print(f"PRODUCTION MONITORING REPORT - {results['timestamp']}")
        print(f"{'='*60}")
        print(f"Overall Status: {status.upper()}")
        
        if results['overall_status']['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in results['overall_status']['critical_issues']:
                print(f"  • {issue}")
        
        if results['overall_status']['warnings']:
            print(f"\n⚠️  WARNINGS:")
            for warning in results['overall_status']['warnings']:
                print(f"  • {warning}")
        
        print(f"\n📊 METRICS:")
        health = results['health']
        if 'response_time' in health:
            print(f"  • Response Time: {health['response_time']:.3f}s")
        
        if results['logs']['status'] == 'analyzed':
            logs = results['logs']
            print(f"  • Recent Errors: {logs['errors']}")
            print(f"  • Recent Warnings: {logs['warnings']}")
        
        print(f"\n{'='*60}")

def main():
    """Main monitoring function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        json_output = True
    else:
        json_output = False
    
    monitor = ProductionMonitor()
    results = monitor.run_full_check()
    
    # Log the results
    status = results['overall_status']['status']
    monitor.log_message(status.upper(), f"Monitoring check completed - Status: {status}")
    
    if json_output:
        print(json.dumps(results, indent=2))
    else:
        monitor.print_summary(results)
    
    # Exit with appropriate code
    if results['overall_status']['status'] == 'critical':
        sys.exit(2)
    elif results['overall_status']['status'] == 'warning':
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main() 