from fastapi import HTTPException, status


def not_found(resource: str = 'Resource') -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'{resource} not found')


def forbidden() -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient permissions')
