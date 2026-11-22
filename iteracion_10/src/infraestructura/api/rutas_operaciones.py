from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from src.dominio.entidades import Producto, Factura
from src.aplicacion.casos_uso_inventario import ServicioInventario
from src.aplicacion.casos_uso_comercial import ServicioComercial
from src.infraestructura.api.esquemas_validacion import (
    EsquemaProductoCrear,
    EsquemaProductoModificar,
    EsquemaIngresoStock,
    EsquemaProductoRespuesta,
    EsquemaFacturaCrear
)
from src.infraestructura.api.inyector_dependencias import (
    obtener_servicio_inventario,
    obtener_servicio_comercial
)



# ===============================================================================
#  ENRUTADOR DE OPERACIONES COMERCIALES (CAPA 3 - INFRAESTRUCTURA API)
# ===============================================================================
#  DECISIÓN DE DISEÑO (CONTROLADOR LIGERO / THIN CONTROLLER):
#
#   Maneja los endpoints relacionados con Inventario (Productos) y Ventas 
#   (Facturación). Delega toda la validación matemática y lógica a los Casos 
#   de Uso.
# ===============================================================================

router = APIRouter(
    tags=["Operaciones Comerciales e Inventario"]
)


# ----------------------------------------------------
#  1. ENDPOINTS DE INVENTARIO Y CATÁLOGO DE PRODUCTOS
# ----------------------------------------------------

@router.post(
    "/api/productos",
    status_code=status.HTTP_201_CREATED
)
def crear_producto(
    datos: EsquemaProductoCrear,
    servicio: ServicioInventario = Depends(obtener_servicio_inventario)
):
    """
     Da de alta un nuevo producto en el catálogo.
    """
    id_generado = servicio.registrar_producto(datos.model_dump())
    
    return {
        "id": id_generado,
        "mensaje": "Producto registrado correctamente."
    }


@router.get(
    "/api/productos",
    response_model=List[EsquemaProductoRespuesta],
    status_code=status.HTTP_200_OK
)
def listar_todos_los_productos(
    servicio: ServicioInventario = Depends(obtener_servicio_inventario)
):
    """
     Devuelve el catálogo completo de productos activos incluyendo su ubicación en depósito.
    """
    productos = servicio.listar_productos()
    
    return [
        EsquemaProductoRespuesta(
            id=p.id,
            codigo=p.codigo,
            descripcion=p.descripcion,
            categoria=p.categoria,
            id_proveedor=p.id_proveedor,
            precio_costo=p.precio_costo,
            precio_venta=p.precio_venta,
            stock_actual=p.stock_actual,
            stock_minimo=p.stock_minimo,
            ubicacion=p.ubicacion,
            vencimiento=p.vencimiento,
            habilitado=p.habilitado
        ) for p in productos
    ]


@router.get(
    "/api/productos/{id_producto}",
    response_model=EsquemaProductoRespuesta,
    status_code=status.HTTP_200_OK
)
def obtener_producto(
    id_producto: int,
    servicio: ServicioInventario = Depends(obtener_servicio_inventario)
):
    """
     Recupera los datos físicos, de ubicación y comerciales de un producto por su ID.
    """
    with servicio.uow:
        producto = servicio.uow.productos.obtener_por_id(id_producto)
        
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró un producto activo con ID {id_producto}."
            )
            
        return EsquemaProductoRespuesta(
            id=producto.id,
            codigo=producto.codigo,
            descripcion=producto.descripcion,
            categoria=producto.categoria,
            id_proveedor=producto.id_proveedor,
            precio_costo=producto.precio_costo,
            precio_venta=producto.precio_venta,
            stock_actual=producto.stock_actual,
            stock_minimo=producto.stock_minimo,
            ubicacion=producto.ubicacion,
            vencimiento=producto.vencimiento,
            habilitado=producto.habilitado
        )


@router.put(
    "/api/productos/{id_producto}",
    status_code=status.HTTP_200_OK
)
def modificar_producto(
    id_producto: int,
    datos: EsquemaProductoModificar,
    servicio: ServicioInventario = Depends(obtener_servicio_inventario)
):
    """
     Actualiza los datos comerciales y de ubicación de un producto.
    """
    servicio.modificar_producto(
        id_producto=id_producto,
        datos=datos.model_dump(exclude_unset=True)
    )
    
    return {"mensaje": "Producto actualizado comercialmente."}


@router.post(
    "/api/productos/{id_producto}/stock",
    status_code=status.HTTP_200_OK
)
def ingresar_stock(
    id_producto: int,
    payload: EsquemaIngresoStock,
    servicio: ServicioInventario = Depends(obtener_servicio_inventario)
):
    """
     Endpoint atómico y seguro para sumar o restar mercadería al inventario.
    """
    servicio.registrar_ingreso_stock(id_producto, payload.cantidad)
    
    return {"mensaje": f"Se ingresaron {payload.cantidad} unidades al producto {id_producto}."}


@router.delete(
    "/api/productos/{id_producto}",
    status_code=status.HTTP_200_OK
)
def eliminar_producto(
    id_producto: int,
    servicio: ServicioInventario = Depends(obtener_servicio_inventario)
):
    """
     Ejecuta una baja lógica de un producto del catálogo.
    """
    servicio.dar_de_baja_producto(id_producto)
    
    return {"mensaje": "Producto dado de baja del catálogo."}


# ----------------------------------------
#  2. ENDPOINTS COMERCIALES (FACTURACIÓN)
# ----------------------------------------

@router.post(
    "/api/facturas",
    status_code=status.HTTP_201_CREATED
)
def emitir_factura(
    datos: EsquemaFacturaCrear,
    servicio: ServicioComercial = Depends(obtener_servicio_comercial)
):
    """
     Orquesta una venta descontando stock atómicamente.
    """
    id_factura = servicio.emitir_factura(
        id_vendedor=datos.id_vendedor,
        id_cliente=datos.id_cliente,
        id_producto=datos.id_producto,
        cantidad=datos.cantidad,
        descuento=datos.descuento
    )
    
    return {
        "id_factura": id_factura,
        "mensaje": "Factura emitida y stock descontado exitosamente."
    }


@router.get(
    "/api/facturas",
    status_code=status.HTTP_200_OK
)
def listar_todas_las_facturas(
    servicio: ServicioComercial = Depends(obtener_servicio_comercial)
):
    """
     Devuelve el historial contable completo de comprobantes activos.
    """
    facturas = servicio.listar_facturas()
    return facturas


@router.delete(
    "/api/facturas/{id_factura}",
    status_code=status.HTTP_200_OK
)
def anular_factura(
    id_factura: int,
    servicio: ServicioComercial = Depends(obtener_servicio_comercial)
):
    """
     Anula un comprobante emitido previamente y restituye el stock.
    """
    servicio.anular_factura(id_factura)
    return {"mensaje": "Factura anulada. El stock fue restituido al inventario."}