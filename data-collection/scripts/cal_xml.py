# def parse_calculation_arcs(content):
#     root = ET.fromstring(content)
#     ns = {'link': 'http://www.xbrl.org/2003/linkbase'}
    
#     equations = []
#     for arc in root.findall('.//link:calculationArc', ns):
#         from_element = arc.attrib['{http://www.w3.org/1999/xlink}from']
#         to_element = arc.attrib['{http://www.w3.org/1999/xlink}to']
#         weight = arc.attrib.get('weight', '1')
#         equations.append(f"{to_element} = {weight} * {from_element}")
#     return equations

import requests
import xml.etree.ElementTree as ET
from collections import defaultdict
from headers import headers
import re

def get_part_before_pattern(input_string):
    # Use regular expression to find the pattern _ followed by two numbers
    pattern = r'_(?=\d{2,}|[^\d_])[\w-]+'
    pattern2 = r'_\d{2,}'
    match = re.search(pattern, input_string)
    # print(input_string)
    # print(match)
    new_string = input_string.rsplit("_", 1)[0]
    if new_string.startswith("loc_"):
        new_string = new_string[len("loc_"):] 
    return new_string
    
def fetch_file_content(url):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.content

def parse_calculation_arcs2(content):
    root = ET.fromstring(content)
    ns = {'link': 'http://www.xbrl.org/2003/linkbase'}
    
    equations = []
    for arc in root.findall('.//link:calculationArc', ns):
        from_element = arc.attrib['{http://www.w3.org/1999/xlink}from']
        to_element = arc.attrib['{http://www.w3.org/1999/xlink}to']
        weight = arc.attrib.get('weight', '1')
        equations.append(f"{to_element} = {weight} * {from_element}")
    return equations

def parse_calculation_arcs(content):
    root = ET.fromstring(content)
    ns = {'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink'
        }
    
    # Store the calculation links in a dictionary for easy reference
    calculations = defaultdict(list)
    stack = []  # Stack to keep track of nested equations

    for link in root.findall('.//link:calculationLink', ns):
        # Find the context reference (e.g., ConsolidatedBalanceSheets)
        context = link.attrib.get('{http://www.w3.org/1999/xlink}label', 'unknown_context')
        # Determine which role this calculation link is for
        role_uri = link.get('{http://www.w3.org/1999/xlink}role')
        main_fact = link.find('link:loc', ns)
        if not main_fact :
            continue
        # print(main_fact)
        main_fact = main_fact.attrib['{http://www.w3.org/1999/xlink}label']
        main_fact = get_part_before_pattern(main_fact)
        recent_from_element = main_fact
        current_equation = main_fact
        if main_fact in calculations:
            # print(calculations[main_fact])
            # print("====")
            if len(calculations[main_fact]) > len(link.findall('link:calculationArc', ns)):
                continue
        calculations[main_fact] = []
        sub_equation = False
        for arc in link.findall('link:calculationArc', ns):
            # remove extra numbers after the last "_" on the right
            from_element = arc.attrib['{http://www.w3.org/1999/xlink}from']
            from_element = get_part_before_pattern(from_element)
            to_element = arc.attrib['{http://www.w3.org/1999/xlink}to']
            to_element = get_part_before_pattern(to_element)
            weight = arc.attrib.get('weight', '1')
            to_element_dict = {'fact': to_element, 'weight': weight}
            # print(to_element_dict)
            # print(from_element, main_fact, role_uri)

            
            while stack and stack[-1]['element'] != from_element:
                stack.pop()  # Unwind the stack to the correct nesting level

            if from_element == main_fact or (stack and from_element == stack[-1]['element']):
                if stack:
                    calculations[stack[-1]['element']].append(to_element_dict)
                else:
                    calculations[main_fact].append(to_element_dict)
            else:
                stack.append({'element': from_element, 'level': len(stack) + 1})
                calculations[from_element].append(to_element_dict)

    # return calculations
    return(dict(calculations))

# def main():
#     base_url = 'https://www.sec.gov/Archives/edgar/data/917851/000110465922046078/'
#     file = 'vale-20211231_cal.xml'

#     file_url = base_url + file
#     content = fetch_file_content(file_url)
#     all_equations = parse_calculation_arcs(content)
#     print(all_equations)


# if __name__ == "__main__":
#     main()