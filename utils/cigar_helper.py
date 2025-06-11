def buff_calc(data):
    exp_count = len(data.get('experience', [])) # experience count
    proj_count = len(data.get('projects', [])) # project count
    educ_count = len(data.get('education', [])) # education count
    cert_count = len(data.get('certifications', [])) # certification count
    ref_count = len(data.get('references', [])) # references count
    awards_count = len(data.get('awards', [])) # awards count

    exp_buff_param = 0.2 if exp_count > 4 else 0.15
    proj_buff_param = 0.2 if proj_count > 2 else 0
    educ_buff_param = 0.18 if educ_count > 2 else 0
    cert_buff_param = 0.15 if cert_count > 3 else 0
    ref_buff_param = 0.15 if ref_count > 3 else 0
    awards_buff_param = 0.15 if ref_count > 3 else 0

    # for experience buff calc
    buffer = (exp_count / 4) * exp_buff_param

    if proj_buff_param > 0:
        buffer = ((proj_count / 2) * proj_buff_param) * buffer
        buffer += buffer

    if educ_buff_param > 0:
        buffer = ((educ_count / 2) * educ_buff_param) * buffer
        buffer += buffer

    if cert_buff_param > 0:
        buffer = ((cert_count / 2) * cert_buff_param) * buffer
        buffer += buffer

    if ref_buff_param > 0:
        buffer = ((ref_count / 2) * ref_buff_param) * buffer
        buffer += buffer

    if awards_buff_param > 0:
        buffer = ((awards_count / 2) * awards_buff_param) * buffer
        buffer += buffer

    return buffer

def increment_calc(data):
    exp = data.get('experience', [])
    increment = (len(exp) // 2) * 50
    
    # just for python notes in for loop...
    # increment = 0
    # for i in range(0, len(exp), 3):
    #     increment += 50

    return increment
        