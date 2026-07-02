import json
import re
import os

def highlight_text(text):
    if not text:
        return ""
    
    # 1. Format bullet points and lists before highlighting
    lines = text.split('\n')
    html_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('* '):
            if not in_list:
                html_lines.append('<ul style="margin-left: 1.5rem; list-style-type: square; margin-top: 8px; margin-bottom: 8px; line-height: 1.6;">')
                in_list = True
            li_content = line[2:]
            # Bold the prefix before the colon
            li_content = re.sub(r'^(.*?):', r'<strong>\1:</strong>', li_content)
            html_lines.append(f'<li style="margin-bottom: 4px;">{li_content}</li>')
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            
            # If it starts with a number like "1. "
            if re.match(r'^\d+\.\s', line):
                html_lines.append(f'<div style="font-weight: bold; margin-top: 12px; margin-bottom: 4px;">{line}</div>')
            else:
                html_lines.append(f'<div style="margin-bottom: 8px; line-height: 1.6;">{line}</div>')
                
    if in_list:
        html_lines.append('</ul>')
        
    html = "\n".join(html_lines)
    
    # 2. Add retro highlighting (underlines and bolds)
    # Highlight dates (e.g., November 13, 2025, May 2027)
    html = re.sub(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b', 
                  r'<u style="text-decoration: underline; text-underline-offset: 2px; text-decoration-color: #A0A090;">\g<0></u>', html)
    html = re.sub(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', 
                  r'<u style="text-decoration: underline; text-underline-offset: 2px; text-decoration-color: #A0A090;">\g<0></u>', html)
                  
    # Highlight sections/rules (e.g., Section 11, Rule 22, Part B)
    html = re.sub(r'\b(Section\s+\d+[A-Z]?)\b', r'<strong>\g<1></strong>', html, flags=re.IGNORECASE)
    html = re.sub(r'\b(Rule\s+\d+[A-Z]?)\b', r'<strong>\g<1></strong>', html, flags=re.IGNORECASE)
    html = re.sub(r'\b(Part\s+[A-Z]+)\b', r'<strong>\g<1></strong>', html, flags=re.IGNORECASE)
    
    return html

def make_clause_content(node):
    """
    Build the HTML content for a clause. 
    If the node has a title but no content, the title becomes the content.
    If it has both, title appears as a bold heading above the content.
    """
    title = node.get("title", "")
    text = node.get("content", "").strip()
    
    parts = []
    if title and not text:
        # Title-only node: display the title as the content
        parts.append(f'<span style="font-weight:700;">{title}</span>')
    elif title and text:
        # Both title and content: show title as sub-heading
        parts.append(f'<span style="font-weight:700; display:block; margin-bottom:6px;">{title}</span>')
        parts.append(highlight_text(text))
    elif text:
        parts.append(highlight_text(text))
    else:
        parts.append(f'<span style="color:var(--text-muted); font-style:italic;">(no content)</span>')
    
    return "\n".join(parts)


def convert_to_actdata(node):
    """
    Map newtry.json (4-level: chapter > section > sub-section > leaf) 
    to the viewer template schema (chapter > section > clause > sub_clause).
    
    Hierarchy mapping:
      JSON level 1 (e.g. "1")        -> chapter
      JSON level 2 (e.g. "1.1")      -> section
      JSON level 3 (e.g. "2.1")      -> section (if has children = sub-sections)
                                         OR clause (if leaf with content)
      JSON level 4 (e.g. "2.1.1")    -> clause
    """
    actData = {"chapter": []}
    
    for ch in node.get("children", []):
        chapter = {
            "chapter_number": ch.get("name", ""),
            "title": ch.get("title", ""),
            "section": []
        }
        
        for sec in ch.get("children", []):
            sec_children = sec.get("children", [])
            sec_content = sec.get("content", "").strip()
            
            section = {
                "section_number": sec.get("name", ""),
                "title": sec.get("title", ""),
                "clauses": []
            }
            
            # Case 1: Section is a pure leaf node (has content, no children)
            if sec_content and not sec_children:
                cl = {
                    "clause_number": "(1)",
                    "title": "",
                    "content": highlight_text(sec_content)
                }
                section["clauses"].append(cl)
            
            # Case 2: Section has own content AND children
            elif sec_content and sec_children:
                # Add section's own content as first clause
                cl = {
                    "clause_number": "(intro)",
                    "title": "",
                    "content": highlight_text(sec_content)
                }
                section["clauses"].append(cl)
                # Then add sub-sections as clauses
                for clause in sec_children:
                    cl = build_clause(clause)
                    section["clauses"].append(cl)
            
            # Case 3: Section has only children (no direct content)
            elif sec_children:
                for clause in sec_children:
                    cl = build_clause(clause)
                    section["clauses"].append(cl)
            
            # Case 4: Empty section with title only
            else:
                cl = {
                    "clause_number": "—",
                    "title": "",
                    "content": f'<span style="color:var(--text-muted); font-style:italic;">{sec.get("title", "")} — no detailed content available.</span>'
                }
                section["clauses"].append(cl)
            
            chapter["section"].append(section)
            
        actData["chapter"].append(chapter)
        
    return actData


def build_clause(clause):
    """
    Build a clause dict from a JSON node at level 3 (e.g. "2.1").
    If this node itself has children (level 4), they become sub_clauses.
    The clause's own content/title is the top-level content.
    """
    clause_children = clause.get("children", [])
    clause_content = clause.get("content", "").strip()
    clause_title = clause.get("title", "")
    name = clause.get("name", "")
    num = f"({name.split('.')[-1]})" if "." in name else f"({name})"
    
    cl = {
        "clause_number": num,
        "title": clause_title,
        "content": "",
        "sub_clauses": []
    }
    
    # Build the main content for this clause
    if clause_title and clause_content:
        cl["content"] = f'<strong style="display:block; margin-bottom:6px;">{clause_title}</strong>' + highlight_text(clause_content)
    elif clause_content:
        cl["content"] = highlight_text(clause_content)
    elif clause_title:
        cl["content"] = f'<strong>{clause_title}</strong>'
    else:
        cl["content"] = f'<span style="color:var(--text-muted);">{num}</span>'
    
    # Map level-4 children as sub_clauses
    if clause_children:
        for sub in clause_children:
            sub_name = sub.get("name", "")
            sub_num_parts = sub_name.split(".")
            sub_num = f"({sub_num_parts[-1]})" if sub_num_parts else f"({sub_name})"
            sub_title = sub.get("title", "")
            sub_content = sub.get("content", "").strip()
            
            sub_html = ""
            if sub_title and sub_content:
                sub_html = f'<strong style="display:block; margin-bottom:4px;">{sub_title}</strong>' + highlight_text(sub_content)
            elif sub_content:
                sub_html = highlight_text(sub_content)
            elif sub_title:
                sub_html = f'<strong>{sub_title}</strong>'
            
            sub_clause = {
                "sub_clause_number": sub_num,
                "content": sub_html
            }
            cl["sub_clauses"].append(sub_clause)
    
    # Remove empty sub_clauses list if nothing was added
    if not cl["sub_clauses"]:
        del cl["sub_clauses"]
    
    return cl


if __name__ == "__main__":
    with open('newtry.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    actData = convert_to_actdata(data)
    actData_json = json.dumps(actData, indent=2)
    
    # Read the viewer_template
    with open('viewer_template.html', 'r', encoding='utf-8') as f:
        template = f.read()
        
    # Inject actData
    final_html = template.replace('const actData = {}', f'const actData = {actData_json};')
    
    # Save the new viewer
    with open('newtry_viewer.html', 'w', encoding='utf-8') as f:
        f.write(final_html)
        
    print("Successfully generated newtry_viewer.html with Retro Typewriter styling.")
