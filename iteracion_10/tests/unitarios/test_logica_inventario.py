# =================================================================================
#  PRUEBAS UNITARIAS: LÓGICA DE INVENTARIO Y COMERCIAL (TDD CICLO 1 - DOMINIO)
# =================================================================================
#  DECISIÓN DE DISEÑO (ALTA COHESIÓN Y TDD):
#
#   Verificamos que las entidades puras (Producto, Factura) calculen correctamente
#   sus estados antes de interactuar con la base de datos. Si una regla de 
#   negocio cambia (ej. cómo se aplica un descuento), solo falla este test y 
#   se corrige en la entidad, sin tocar el servidor ni las vistas.
# =================================================================================



import pytest
from src.dominio.entidades import Producto, Factura


# ---------------------------------------------------
#  1. TESTS REGLAS DE NEGOCIO: PRODUCTO (INVENTARIO)
# ---------------------------------------------------

def test_producto_tiene_stock_suficiente():
    """
     Verifica que la entidad autorice la venta si la cantidad demandada 
     es menor al stock disponible en el sistema.
    """
    producto = Producto(
        codigo="TEST-001",
        descripcion="Monitor 24",
        categoria="Monitores",
        id_proveedor=1,
        precio_costo=100.0,
        precio_venta=150.0,
        stock_actual=10.0
    )
    
    assert producto.hay_stock_suficiente(5.0) is True


def test_producto_autoriza_venta_si_stock_queda_en_cero():
    """
     Verifica el límite de borde: vender exactamente todo el stock actual
     es una operación válida en el dominio.
    """
    producto = Producto(
        codigo="TEST-002",
        descripcion="Teclado",
        categoria="Periféricos",
        id_proveedor=1,
        precio_costo=20.0,
        precio_venta=40.0,
        stock_actual=5.0
    )
    
    assert producto.hay_stock_suficiente(5.0) is True


def test_producto_rechaza_venta_por_stock_insuficiente():
    """
     Verifica que la entidad rechace la operación si se piden más unidades 
     de las que existen, previniendo stocks negativos físicos.
    """
    producto = Producto(
        codigo="TEST-003",
        descripcion="Mouse",
        categoria="Periféricos",
        id_proveedor=1,
        precio_costo=10.0,
        precio_venta=25.0,
        stock_actual=3.0
    )
    
    assert producto.hay_stock_suficiente(10.0) is False


# -------------------------------------------------
#  2. TESTS REGLAS DE NEGOCIO: FACTURA (COMERCIAL)
# -------------------------------------------------

def test_factura_calcula_total_sin_descuento():
    """
     Garantiza que el subtotal se calcule correctamente (cantidad * valor) 
     cuando no hay descuentos aplicados.
    """
    factura = Factura(
        id_vendedor=1,
        id_cliente=2,
        id_producto=3,
        cantidad=4.0,
        valor=250.0,  # 4 * 250 = 1000
        descuento=0.0
    )
    
    total = factura.calcular_total_estimado()
    assert total == 1000.0


def test_factura_calcula_total_con_descuento_porcentual():
    """
     Garantiza que la fórmula de descuento comercial se aplique correctamente 
     sobre el subtotal en memoria, emulando la lógica del motor SQLite.
    """
    factura = Factura(
        id_vendedor=1,
        id_cliente=2,
        id_producto=3,
        cantidad=10.0,
        valor=100.0,  # Subtotal: 1000.
        descuento=20.0  # 20% de descuento -> Total esperado: 800.
    )
    
    total = factura.calcular_total_estimado()
    assert total == 800.0