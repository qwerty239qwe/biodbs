

def parse_cmp(cmp_dics: dict):
    new_dic = {}

    for cmp_dic in cmp_dics:
        if "TOCHeading" in cmp_dic:
            new_key = cmp_dic["TOCHeading"]
            if "Section" in cmp_dic:
                new_val = parse_cmp(cmp_dic["Section"])
            elif "Information" in cmp_dic:
                new_val = parse_cmp(cmp_dic["Information"])
            else:
                raise ValueError()
            new_dic[new_key] = new_val
    if len(new_dic) == 0:
        return cmp_dics
    return new_dic