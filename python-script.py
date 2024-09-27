import yaml

def load_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def save_yaml(data, file_path):
    with open(file_path, 'w') as file:
        yaml.dump(data, file, default_flow_style=False, sort_keys=False)

def process_item(path, item, env_vars, placeholder_dict, root_dict):
    if isinstance(item, dict):
        for k, v in item.items():
            # Ensuring placeholder_dict[k] exists
            if k not in placeholder_dict:
                placeholder_dict[k] = {}
            process_item(f"{path}_{k}" if path else k, v, env_vars, placeholder_dict[k], root_dict)
    else:
        # Formatted environment variable key
        formatted_key = f"{prefix}_{path.upper().replace('-', '_').replace(' ', '_')}"
        env_vars[formatted_key] = item
        # Set the placeholder in the original dictionary structure
        keys = path.split('_')
        target_dict = root_dict
        for key in keys[:-1]:
            target_dict = target_dict[key]
        target_dict[keys[-1]] = f"${{{formatted_key}}}"

def convert_yaml_to_env_vars(file_path, prefix, output_env_path, output_placeholder_path):
    data = load_yaml(file_path)
    env_vars = {}
    placeholders = yaml.load(yaml.dump(data), Loader=yaml.FullLoader)  # Deep copy for placeholders

    for key, value in data.items():
        process_item(key, value, env_vars, placeholders[key], placeholders)

    # Save the environment variables and placeholders to files
    save_yaml(env_vars, output_env_path)
    save_yaml(placeholders, output_placeholder_path)

    print(f"Environment variables written to {output_env_path}")
    print(f"Placeholders written to {output_placeholder_path}")

# Example usage settings
prefix = "SECRET_TRLRS"
file_path = './pd_trilrs.yml'  # Ensure you provide the correct path
output_env_path = './pd_env.yml'
output_placeholder_path = './pd_placeholders.yml'

convert_yaml_to_env_vars(file_path, prefix, output_env_path, output_placeholder_path)