#!/usr/bin/env python3
"""
Test script to validate configuration loading and structure.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config_loader import AnalysisConfig


def test_config_loading():
    """Test configuration loading."""
    print("=" * 60)
    print("Testing Configuration Loading")
    print("=" * 60)
    print()

    try:
        # Load configuration
        config = AnalysisConfig("config.yaml")
        print("✓ Configuration file loaded successfully")
        print()

        # List available analysis types
        analysis_types = config.list_available_analysis_types()
        print(f"Available analysis types: {', '.join(analysis_types)}")
        print()

        # Load basket pages configuration
        basket_config = config.get_analysis_type("basket_pages")
        print(f"Analysis Type: {basket_config.name}")
        print(f"Description: {basket_config.description}")
        print()

        # Display criteria
        print(f"Number of criteria: {len(basket_config.criteria)}")
        print()
        print("Criteria breakdown:")
        print("-" * 60)

        total_weight = sum(c.weight for c in basket_config.criteria)
        for criterion in basket_config.criteria:
            print(f"\n{criterion.name} (ID: {criterion.id})")
            print(f"  Weight: {criterion.weight}/10")
            print(f"  Description: {criterion.description}")
            print(f"  Evaluation points: {len(criterion.evaluation_points)}")
            print(f"  Benchmarks: {len(criterion.benchmarks)}")

        print()
        print(f"Total weight sum: {total_weight}")
        print()

        # Display screenshot configuration
        print("Screenshot Configuration:")
        print("-" * 60)
        print(f"Full page capture: {basket_config.screenshot_config.full_page}")
        print(f"Capture states: {', '.join(basket_config.screenshot_config.capture_states)}")
        print(f"\nViewports:")
        for viewport in basket_config.screenshot_config.viewports:
            print(f"  - {viewport.name}: {viewport.width}x{viewport.height}")

        print()
        print("=" * 60)
        print("✓ Configuration test completed successfully!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"✗ Error loading configuration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_config_loading()
    sys.exit(0 if success else 1)
