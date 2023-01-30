import jaro
import numpy as np


def compare_postcode(pc, pc2):
    """
    Function to compare the similarity in 2 postcodes.
    If they are exactly the same, then confidence is 1
    If one postcode is only half complete (Postcode Area, e.g. "BN1" rather than "BN1 2BC"),
    but the first halves are the same, then confidence is 0.5
    If they are both complete postcodes, and the first half and next number is the same (Postcode Sector,
    e.g. "BN1 2" rather than "BN1 2BC"), then confidence is 0.5
    Otherwise, confidence is 0
    :param pc: First postcode to compare
    :param pc2: Second postcode to compare
    :return: Postcode confidence (as described above)
    """

    # Full Postcode
    pc = pc.strip(' ').replace('  ', ' ').lower()
    pc2 = pc2.strip(' ').replace('  ', ' ').lower()

    # First Half Of Postcode (Postcode Area)
    pc_half = pc.split(' ')[0]
    pc2_half = pc2.split(' ')[0]

    # Second Half Of Postcode
    pc_half_2 = pc.split(' ')[1] if len(pc.split(' ')) >= 2 else np.nan
    pc2_half_2 = pc2.split(' ')[1] if len(pc2.split(' ')) >= 2 else np.nan

    # return the confidence level in postcode - 1 for full postcode match. 0.5 for half match. 0 for no match
    if pc == pc2:
        return 1
    elif (pc_half == pc2_half) and ((type(pc_half_2) != str) or (type(pc2_half_2) != str)):
        print('HALF MATCH')
        return 0.5
    elif (pc_half == pc2_half) and (pc_half_2[0] == pc2_half_2[0]):
        print('HALF MATCH')
        return 0.5
    else:
        return 0


"""
    # FOR VIEWING ERRORS - need "try" statement on if statements above to work
    except IndexError:
        print(pc, pc2, 'INDEX ERROR')
        print(pc_half_2, pc2_half_2, 'ERROR')
        exit()
    except TypeError:
        print(pc, pc2, 'TYPE ERROR')
        print(pc_half_2, pc2_half_2, 'ERROR')
        exit()
"""


def find_correct_result(data, gid):
    """
    Check the results returned by the the Food Standards Authority API and determine which result - if any - is the correct one.
    Check the name and postcode from the original Google record, and the results from FSA API to see if they are similar
    enough to determine as a match.
    :param data: Dictionary containing the list of establishment's returned by FSA API, and details of the original Google
    record that was queried
    :param gid: Google ID of record
    :return: Result and confidence if a match is found, else return NaN
    """

    name = data['name']
    pc = data['postcode']
    # add = data['location']
    results = data['results']

    if len(results) != 0:

        for res in results:
            name2 = res["BusinessName"]
            pc2 = res["PostCode"]

            pc_confidence = compare_postcode(pc, pc2)

            jaro_score = jaro.jaro_winkler_metric(name, name2)

            print(name, pc)
            print(name2, pc2)
            print('{0} Postcode confidence and {1} jaro-winkler similarity\n'.format(pc_confidence, jaro_score))

            if (pc_confidence==1 and jaro_score >= 0.7) or (pc_confidence==0.5 and jaro_score >= 0.85):
                print('\n\n')
                return res, pc_confidence

        print('\n\n')
        return np.nan, np.nan

    else:
        print(name, pc)
        print('No Results \n\n')
        return np.nan, np.nan
