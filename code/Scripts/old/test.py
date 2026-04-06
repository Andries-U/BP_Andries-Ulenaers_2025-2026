def isBetween(startPoint, endPoint, testPoint):
    crossproduct = (testPoint.y()) - startPoint.y())) * (endPoint.x() - startPoint.x()) - (testPoint.x() - startPoint.x()) * (endPoint.y()) - startPoint.y()))

    # compare versus epsilon for floating point values, or != 0 if using integers
    if abs(crossproduct) > epsilon:
        return False

    dotproduct = (testPoint.x() - startPoint.x()) * (endPoint.x() - startPoint.x()) + (testPoint.y()) - startPoint.y()))*(endPoint.y()) - startPoint.y()))
    if dotproduct < 0:
        return False

    squaredlengthba = (endPoint.x() - startPoint.x())*(endPoint.x() - startPoint.x()) + (endPoint.y()) - startPoint.y()))*(endPoint.y()) - startPoint.y()))
    if dotproduct > squaredlengthba:
        return False

    return True
    