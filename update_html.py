import re

def update_file(path, fetch_url):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Replace const actData = ... with let actData = {};
    text = re.sub(r'const actData\s*=\s*\{.*?\};', 'let actData = {};', text, flags=re.DOTALL)
    
    # Replace renderApp(); with the fetch block
    fetch_block = f'''
        fetch('{fetch_url}')
            .then(res => res.json())
            .then(data => {{
                actData = data;
                renderApp();
            }})
            .catch(err => console.error("Failed to load data:", err));
    '''
    text = re.sub(r'(?<!function )\brenderApp\(\);', fetch_block, text)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

update_file('c:/Users/avijn_th5xjtu/Desktop/code/dp2/new/dpdp_fastapi/templates/framework.html', '/data/newtry.json')
update_file('c:/Users/avijn_th5xjtu/Desktop/code/dp2/new/dpdp_fastapi/templates/dpdpact.html', '/data/raw/dpdp_titled.json')
