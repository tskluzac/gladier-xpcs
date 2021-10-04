

class ConciergeError(Exception):
    pass

class MDFSubmissionError(Exception):
    """There was some unforeseen error submitting to the MDF"""
    pass


class MDFPreviousSubmission(MDFSubmissionError):
    """This dataset has already been submitted to the MDF"""
    pass


class MDFAccessDenied(MDFSubmissionError):
    pass


class MDFTokenAbsent(MDFSubmissionError):
    """User token store has no mdf token!"""
    pass
