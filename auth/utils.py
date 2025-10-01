from passlib.context import CryptContext

# Create a password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        password (str): Plain text password
        hashed (str): Hashed password from database
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(password, hashed)

