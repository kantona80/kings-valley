# Formato del fichero de salida:

## Campos fijos:

* Tiles horizontales del mapa (1 byte)
* Tiles verticales del mapa (1 byte)
* Tiles de fondo (tiles horizontales * tiles verticales * 1 byte)
* Tiles de primer plano (tiles horizontales * tiles verticales * 1 byte)
* Número de campos variables (1 byte)

## Campos variables

1 letra seguida de 3 o más bytes:

Daga: (4 bytes total)

    Dxyt
    
    D   Identificador
    x   Coordenada x
    y   Coordenada y
    t   Tipo: Valor del ID del tile

Pico: (4 bytes total)

    Pxyt
    
    P   Identificador
    x   Coordenada x
    y   Coordenada y
    t   Tipo: Valor del ID del tile

Joya: (4 bytes total)

    Jxyt

    J   Identificador
    x   Coordenada x
    y   Coordenada y
    t   Tipo: Valor del ID del tile

Puerta: (4 bytes total)

    Txyt

    T   Identificador
    x   Coordenada x
    y   Coordenada y
    t   Tipo:
        - 0: Entrada
        - 1: Salida
        - 2: Entrada y Salida (Primer nivel)

Giratoria (Puerta): (5 bytes total)

    Gxyht

    G   Identificador
    x   Coordenada x
    y   Coordenada y
    h   Cuadros en vertical
    t   Lugar hacia donde gira:
        - 0: Gira a la derecha
        - 1: Gira a la izquierda

Escaleras: (4 bytes total)

    Exyt

    E   Identificador
    x   Coordenada x
    y   Coordenada y
    t   Tipo:
        - 0: sube-derecha
        - 1: baja-izquierda
        - 2: sube-izquierda
        - 3: baja-derecha

Momia: (4 bytes total)

    Mxyt

    M   Identificador
    x   Coordenada x
    y   Coordenada y
    t   Tipo: 
        - 0: Blanca
        - 1: Azul
        - 2: Amarilla
        - 3: Naranja
        - 4: Roja

Muro: (5 bytes total)

    Uabcd

    U   Identificador
    a   Coordenada x
    b   Coordenada y1
    c   Coordenada y2
    d   Coordenada x del tile de activación

