# zeus
def buff_calc(data):
    exp_count = len(data.get('experience', [])) # experience count
    proj_count = len(data.get('projects', [])) # project count
    educ_count = len(data.get('education', [])) # education count
    cert_count = len(data.get('certifications', [])) # certification count
    ref_count = len(data.get('references', [])) # references count
    awards_count = len(data.get('awards', [])) # awards count

    exp_buff_param = 0.9 if exp_count > 4 else 0.75
    proj_buff_param = 0.45 if proj_count > 2 else 0.3
    educ_buff_param = 0.35 if educ_count > 2 else 0.25
    cert_buff_param = 0.35 if cert_count > 3 else 0.25
    ref_buff_param = 0.35 if ref_count > 3 else 0.25
    awards_buff_param = 0.25 if ref_count > 3 else 0.20

    buffer = 0
    if exp_count >= 3:
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
    else:
        buffer = 0.75

    return buffer