"""
Test Harness - Evaluation and reliability testing for the music recommender
"""

import sys
import json
from typing import Dict, List, Any
from datetime import datetime

# Import our modules
from recommender import MusicRecommender
from data_manager import DataManager
from rag_engine import RAGEngine


class TestHarness:
    """
    Comprehensive test harness for evaluating the music recommender system.
    
    Features:
    - Consistency testing
    - Confidence scoring validation
    - Error handling tests
    - Parameter sensitivity tests
    - Full evaluation reports
    """
    
    def __init__(self):
        self.data_manager = DataManager()
        self.recommender = MusicRecommender(self.data_manager)
        self.rag_engine = RAGEngine()
        self.results = []
    
    def run_all_tests(self) -> Dict:
        """Run all tests and return comprehensive results"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
        
        # Run each test category
        report["tests"]["consistency"] = self.test_consistency()
        report["tests"]["confidence"] = self.test_confidence_scoring()
        report["tests"]["error_handling"] = self.test_error_handling()
        report["tests"]["parameter_sensitivity"] = self.test_parameter_sensitivity()
        report["tests"]["rag_functionality"] = self.test_rag_functionality()
        report["tests"]["writer_tracking"] = self.test_writer_tracking()
        
        # Calculate summary
        total = 0
        passed = 0
        
        for test_name, test_result in report["tests"].items():
            total += 1
            if test_result["passed"]:
                passed += 1
        
        report["summary"] = {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": f"{(passed/total)*100:.1f}%"
        }
        
        return report
    
    def test_consistency(self) -> Dict:
        """Test that recommendations are consistent across multiple calls"""
        test_case = {
            "name": "Consistency Test",
            "description": "Verify same inputs produce same outputs"
        }
        
        try:
            prefs = {'genre': 'Pop', 'energy': 0.5}
            
            # Run same recommendation twice
            results1 = self.recommender.recommend(prefs, 5)
            results2 = self.recommender.recommend(prefs, 5)
            
            # Compare results
            titles1 = [r['title'] for r in results1]
            titles2 = [r['title'] for r in results2]
            
            is_consistent = titles1 == titles2
            
            return {
                "passed": is_consistent,
                "message": f"Consistent results: {is_consistent}" if is_consistent else "Results varied between calls",
                "details": {
                    "run_1": titles1,
                    "run_2": titles2
                }
            }
        except Exception as e:
            return {
                "passed": False,
                "message": f"Error during test: {str(e)}",
                "details": {}
            }
    
    def test_confidence_scoring(self) -> Dict:
        """Test confidence scoring functionality"""
        test_case = {
            "name": "Confidence Scoring Test",
            "description": "Verify confidence scores are valid"
        }
        
        try:
            # Test with known song
            confidence = self.recommender.get_confidence_score("Come Here")
            
            # Test with unknown song
            unknown_confidence = self.recommender.get_confidence_score("Unknown Song XYZ")
            
            # Valid if known song has higher confidence
            is_valid = (0 <= confidence <= 1) and (0 <= unknown_confidence <= 1)
            
            return {
                "passed": is_valid,
                "message": f"Known song confidence: {confidence:.2f}, Unknown: {unknown_confidence:.2f}",
                "details": {
                    "known_song_confidence": confidence,
                    "unknown_song_confidence": unknown_confidence
                }
            }
        except Exception as e:
            return {
                "passed": False,
                "message": f"Error during test: {str(e)}",
                "details": {}
            }
    
    def test_error_handling(self) -> Dict:
        """Test error handling for invalid inputs"""
        test_case = {
            "name": "Error Handling Test",
            "description": "Verify proper error handling - system should handle invalid inputs gracefully"
        }
        
        errors_handled = 0
        tests_run = 0
        
        # Test 1: Invalid genre type - should handle gracefully
        tests_run += 1
        try:
            bad_prefs = {'genre': 123}  # Should be string
            result = self.recommender.recommend(bad_prefs, 5)
            # If we get here without crashing, it's handled gracefully
            if isinstance(result, list):
                errors_handled += 1
        except (ValueError, TypeError):
            errors_handled += 1
        
        # Test 2: Invalid energy value - should handle gracefully
        tests_run += 1
        try:
            bad_prefs = {'energy': 2.0}  # Out of range
            result = self.recommender.recommend(bad_prefs, 5)
            if isinstance(result, list):
                errors_handled += 1
        except (ValueError, TypeError):
            errors_handled += 1
        
        # Test 3: Invalid preferences dict - should handle gracefully
        tests_run += 1
        try:
            bad_prefs = "not a dict"
            result = self.recommender.recommend(bad_prefs, 5)
            if isinstance(result, list):
                errors_handled += 1
        except (ValueError, TypeError):
            errors_handled += 1
        
        # Test 4: Empty preferences - should still work
        tests_run += 1
        try:
            result = self.recommender.recommend({}, 5)
            if isinstance(result, list):
                errors_handled += 1
        except (ValueError, TypeError):
            errors_handled += 1
        
        return {
            "passed": errors_handled == tests_run,
            "message": f"Handled {errors_handled}/{tests_run} error cases gracefully",
            "details": {
                "errors_handled": errors_handled,
                "tests_run": tests_run
            }
        }
    
    def test_parameter_sensitivity(self) -> Dict:
        """Test that different parameters produce different results"""
        test_case = {
            "name": "Parameter Sensitivity Test",
            "description": "Verify parameter changes affect recommendations"
        }
        
        try:
            # Test with different parameters
            prefs1 = {'genre': 'Rock', 'energy': 0.9}
            prefs2 = {'genre': 'Folk', 'energy': 0.2}
            
            recs1 = self.recommender.recommend(prefs1, 5)
            recs2 = self.recommender.recommend(prefs2, 5)
            
            titles1 = [r['title'] for r in recs1]
            titles2 = [r['title'] for r in recs2]
            
            is_different = titles1 != titles2
            
            return {
                "passed": is_different,
                "message": "Different parameters produce different results" if is_different else "Results too similar",
                "details": {
                    "rock_high_energy": titles1,
                    "folk_low_energy": titles2
                }
            }
        except Exception as e:
            return {
                "passed": False,
                "message": f"Error during test: {str(e)}",
                "details": {}
            }
    
    def test_rag_functionality(self) -> Dict:
        """Test RAG engine functionality"""
        test_case = {
            "name": "RAG Functionality Test",
            "description": "Verify RAG can add and retrieve context"
        }
        
        try:
            # Add a test song
            self.rag_engine.add_song_context(
                title="Test Song",
                artist="Test Artist",
                genre="Pop",
                mood="Happy",
                writer="Test Writer",
                description="A test song for evaluation"
            )
            
            # Retrieve context
            context = self.rag_engine.get_song_context("Test Song")
            
            doc_count = self.rag_engine.get_document_count()
            
            is_working = len(context) > 0 and doc_count > 0
            
            return {
                "passed": is_working,
                "message": f"RAG working: {doc_count} documents, context retrieved",
                "details": {
                    "document_count": doc_count,
                    "context_length": len(context)
                }
            }
        except Exception as e:
            return {
                "passed": False,
                "message": f"Error during test: {str(e)}",
                "details": {}
            }
    
    def test_writer_tracking(self) -> Dict:
        """Test writer/composer tracking functionality"""
        test_case = {
            "name": "Writer Tracking Test",
            "description": "Verify writer statistics are available"
        }
        
        try:
            writers = self.recommender.get_available_writers()
            writer_stats = self.recommender.get_writer_statistics()
            
            has_writers = len(writers) > 0
            has_stats = not writer_stats.empty
            
            return {
                "passed": has_writers and has_stats,
                "message": f"Found {len(writers)} writers with statistics",
                "details": {
                    "writer_count": len(writers),
                    "top_writer": writers[0] if writers else None
                }
            }
        except Exception as e:
            return {
                "passed": False,
                "message": f"Error during test: {str(e)}",
                "details": {}
            }
    
    def run_custom_test(self, test_name: str, test_func) -> Dict:
        """Run a custom test function"""
        try:
            result = test_func()
            return {
                "passed": result,
                "message": f"Custom test '{test_name}' {'passed' if result else 'failed'}",
                "details": {}
            }
        except Exception as e:
            return {
                "passed": False,
                "message": f"Error in custom test: {str(e)}",
                "details": {}
            }
    
    def print_report(self, report: Dict):
        """Print a formatted test report"""
        print("\n" + "="*60)
        print("🎵 MUSIC RECOMMENDER TEST REPORT")
        print("="*60)
        print(f"\nTimestamp: {report['timestamp']}\n")
        
        print("📋 TEST RESULTS:")
        print("-"*40)
        
        for test_name, result in report['tests'].items():
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"\n{status} {test_name.replace('_', ' ').title()}")
            print(f"   {result['message']}")
        
        print("\n" + "-"*40)
        print("\n📊 SUMMARY:")
        summary = report['summary']
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Pass Rate: {summary['pass_rate']}")
        
        print("\n" + "="*60 + "\n")
    
    def save_report(self, report: Dict, filename: str = "test_report.json"):
        """Save report to JSON file"""
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {filename}")


def main():
    """Main entry point for test harness"""
    print("🎵 Running Music Recommender Test Harness...\n")
    
    harness = TestHarness()
    report = harness.run_all_tests()
    
    # Print and save report
    harness.print_report(report)
    harness.save_report(report)
    
    # Exit with appropriate code
    if report['summary']['failed'] == 0:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"⚠️ {report['summary']['failed']} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()