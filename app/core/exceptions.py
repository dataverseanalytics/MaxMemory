from fastapi import HTTPException, status


class UserAlreadyExistsException(HTTPException):
    """Exception raised when user already exists"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )


class InvalidCredentialsException(HTTPException):
    """Exception raised when credentials are invalid"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


class UserNotFoundException(HTTPException):
    """Exception raised when user is not found"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


class InvalidTokenException(HTTPException):
    """Exception raised when token is invalid or expired"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )


class GoogleAuthException(HTTPException):
    """Exception raised when Google authentication fails"""
    def __init__(self, detail: str = "Google authentication failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
