import cv2


def match_single_template(target_image, template_image):
    """Match a single template in the target image and return location and value if found"""
    result = cv2.matchTemplate(target_image, template_image, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_val, max_loc
