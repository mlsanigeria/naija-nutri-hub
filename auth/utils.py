from passlib.context import CryptContext

# Define the password hashing scheme
# bcrypt is the current best practice for hashing passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hashes a plain-text password using the configured CryptContext.
    """
    # The CryptContext object handles salting and hashing automatically
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compares a plain-text password with a stored hash.

    Args:
        plain_password: The password provided by the user (e.g., during login).
        hashed_password: The securely stored hash retrieved from the database.

    Returns:
        True if the passwords match, False otherwise.
    """
    # The CryptContext object handles the comparison securely
    return pwd_context.verify(plain_password, hashed_password)