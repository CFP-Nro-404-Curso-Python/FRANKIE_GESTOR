import bcrypt
from src.dominio.puertos import PuertoHashing

# =================================================================================
#  ADAPTADOR DE SEGURIDAD (CAPA 3 - INFRAESTRUCTURA)
# =================================================================================
#  DECISIÓN DE DISEÑO (PATRÓN ADAPTADOR Y PRINCIPIO DIP):
#
#   Esta clase es la implementación concreta del contrato 'PuertoHashing' definido 
#   en la Capa de Dominio. Si en el futuro bcrypt queda obsoleto y decidimos 
#   migrar a Argon2, solo creamos un nuevo adaptador. El núcleo de negocio no 
#   sufrirá ninguna modificación, manteniendo el bajo acoplamiento.
# =================================================================================



class AdaptadorBcrypt(PuertoHashing):
    
    def hashear_password(self, password_plana: str) -> str:
        """
         Toma una contraseña en texto plano, genera una "sal" aleatoria (salt) 
         y aplica el algoritmo criptográfico.
        
         Nota técnica (KISS): Bcrypt requiere operar nativamente con bytes. 
         Por eso codificamos el string a 'utf-8' antes de procesarlo y lo 
         decodificamos al salir, permitiendo que el resto del sistema siga 
         manejando strings estándar sin preocuparse por estas conversiones.
        """
        password_bytes = password_plana.encode('utf-8')
        
        # gensalt() incorpora un factor de costo computacional (work factor).
        hash_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        
        return hash_bytes.decode('utf-8')

    def verificar_password(self, password_plana: str, password_hash: str) -> bool:
        """
        Verifica si la contraseña plana ingresada (ej. en el Login) coincide 
        matemáticamente con el hash almacenado en SQLite.
        """
        password_bytes = password_plana.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        
        # checkpw mitiga vulnerabilidades como los ataques de sincronización (timing attacks).
        return bcrypt.checkpw(password_bytes, hash_bytes)