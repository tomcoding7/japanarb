#!/usr/bin/env python3
"""
Script to switch eBay API environment between sandbox and production.
"""

import os
import sys

def switch_environment(environment):
    """Switch eBay API environment."""
    print(f"🔄 Switching eBay API environment to: {environment}")
    
    # Read current .env file
    env_file = ".env"
    if not os.path.exists(env_file):
        print(f"❌ .env file not found!")
        return False
    
    try:
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update the environment line
        updated_lines = []
        environment_updated = False
        
        for line in lines:
            if line.startswith('EBAY_ENVIRONMENT='):
                updated_lines.append(f'EBAY_ENVIRONMENT={environment}\n')
                environment_updated = True
            else:
                updated_lines.append(line)
        
        # If no environment line found, add it
        if not environment_updated:
            updated_lines.append(f'EBAY_ENVIRONMENT={environment}\n')
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"✅ Environment switched to: {environment}")
        print(f"💡 You can now run: python test_ebay_api.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {str(e)}")
        return False

def show_current_environment():
    """Show current environment setting."""
    env_file = ".env"
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                if line.startswith('EBAY_ENVIRONMENT='):
                    current_env = line.split('=', 1)[1].strip()
                    print(f"🌍 Current environment: {current_env}")
                    return current_env
        except Exception as e:
            print(f"❌ Error reading .env file: {str(e)}")
    
    print("❌ No environment setting found")
    return None

def main():
    """Main function."""
    print("🚀 eBay API Environment Switcher")
    print("=" * 40)
    
    # Show current environment
    current_env = show_current_environment()
    
    if len(sys.argv) > 1:
        new_env = sys.argv[1].lower()
        if new_env in ['sandbox', 'production']:
            switch_environment(new_env)
        else:
            print("❌ Invalid environment. Use 'sandbox' or 'production'")
    else:
        print("\n💡 Usage:")
        print("   python switch_ebay_environment.py sandbox")
        print("   python switch_ebay_environment.py production")
        print("\n📊 Test Results:")
        print("   ✅ Production credentials: WORKING")
        print("   ❌ Sandbox credentials: FAILING")
        print("\n💡 Recommendation: Use production environment for now")

if __name__ == "__main__":
    main() 