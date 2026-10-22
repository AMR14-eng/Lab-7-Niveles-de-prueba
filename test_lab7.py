import book
import pytest
import library
import user
import main


# =====================================================================
# FIXTURES (Tema 7)
# El libro "Orgullo y prejuicio" se repetía en varias pruebas,
# así que lo creo una sola vez aquí y lo pido como argumento.
# =====================================================================
@pytest.fixture
def libro():
    return book.Book("Orgullo y prejuicio", "Tenoch M", 2026, "ISBN0001")


@pytest.fixture
def lib_init():
    lib = library.Library()
    book_tenoch = book.Book("Orgullo y prejuicio", "Tenoch M", 2026, "ISBN0001")
    lib.add_book(book_tenoch)
    Tenoch = user.User("Tenoch", "0001")
    lib.add_user(Tenoch)
    return lib


# =====================================================================
# Pruebas básicas de Book
# =====================================================================
@pytest.mark.unit
def test_borrow_book(libro):
    assert libro.title == "Orgullo y prejuicio"
    libro.borrow()
    assert libro.borrowed


@pytest.mark.unit
def test_return_book(libro):
    libro.borrow()
    assert libro.borrowed
    libro.return_book()
    assert libro.borrowed == False


# =====================================================================
# pytest.raises (Tema 9)
# Prestar dos veces el mismo libro es una entrada inválida.
# =====================================================================
@pytest.mark.unit
def test_borrow_two_times_book(libro):
    libro.borrow()
    assert libro.borrowed == True
    with pytest.raises(ValueError, match="The book is already borrowed"):
        libro.borrow()


# =====================================================================
# try-except (Tema 10)
# A) Excepción que se PROPAGA: library.borrow_book no tiene try-except,
#    el error sube hasta la prueba y aquí lo atrapo.
# B) Excepción CAPTURADA: main.run() sí tiene try-except, así que el
#    programa NO truena: solo imprime "Error: ..." y sigue.
# =====================================================================
@pytest.mark.unit
def test_borrow_and_try_exception(lib_init):
    lib = lib_init
    lib.borrow_book("0001", "ISBN0001")
    try:
        lib.borrow_book("0001", "ISBN0001")
        assert False, "Debió lanzar ValueError"
    except ValueError as e:
        assert str(e) == "The book is already borrowed"


@pytest.mark.unit
def test_main_captura_excepcion(monkeypatch, capsys):
    # Respuestas que "escribe" el usuario: opción 1, ISBN, ID inexistente, salir
    respuestas = iter(["1", "ISBN001", "U999", "0"])
    monkeypatch.setattr("builtins.input", lambda mensaje: next(respuestas))

    main.run()  # no truena aunque haya error, porque main lo captura

    salida = capsys.readouterr().out
    assert "Error: User not found" in salida


# =====================================================================
# Marcadores (Temas 4 y 5)
# - "prestamos" es personalizado y está registrado en pytest.ini
#   Ejecutar:  pytest -m prestamos
# - "wip"  Ejecutar:  pytest -m wip
# =====================================================================
@pytest.mark.prestamos
def test_library_init(lib_init):
    lib = lib_init
    lib.borrow_book("0001", "ISBN0001")
    assert lib.books[0].borrowed == True
    assert lib.users[0].get_history() == ["Borrowed: Orgullo y prejuicio"]


@pytest.mark.wip
def test_library_init_ID_not_registered(lib_init):
    lib = lib_init
    with pytest.raises(ValueError, match="User not found"):
        lib.borrow_book("0002", "ISBN0001")


# =====================================================================
# monkeypatch.setattr (Tema 1)
# Pongo "borrowed" en True para simular que alguien más ya lo pidió.
# =====================================================================
@pytest.mark.unit
def test_monkeypatch_setattr(lib_init, monkeypatch):
    lib = lib_init
    monkeypatch.setattr(lib.books[0], "borrowed", True)
    with pytest.raises(ValueError, match="The book is already borrowed"):
        lib.borrow_book("0001", "ISBN0001")


# =====================================================================
# monkeypatch.delattr (Tema 2)
# Elimino temporalmente el método register_borrow de la clase User.
# borrow_book lo necesita, así que debe fallar con AttributeError.
# =====================================================================
@pytest.mark.unit
def test_monkeypatch_delattr(lib_init, monkeypatch):
    lib = lib_init
    monkeypatch.delattr(user.User, "register_borrow")
    with pytest.raises(AttributeError):
        lib.borrow_book("0001", "ISBN0001")


# =====================================================================
# monkeypatch.setitem (Tema 3)
# Cambio settings["loans_enabled"] a False.
# borrow_book debe imprimir el aviso y NO prestar el libro.
# =====================================================================
@pytest.mark.unit
def test_monkeypatch_setitem(lib_init, monkeypatch, capsys):
    lib = lib_init
    monkeypatch.setitem(library.settings, "loans_enabled", False)

    lib.borrow_book("0001", "ISBN0001")

    assert lib.books[0].borrowed == False
    assert capsys.readouterr().out == "Loans are disabled\n"


# =====================================================================
# Parametrize (Tema 6)
# Una sola función, varias entradas inválidas con su error esperado.
# =====================================================================
@pytest.mark.unit
@pytest.mark.parametrize("user_id, isbn, mensaje", [
    ("0002", "ISBN0001", "User not found"),
    ("0001", "ISBN9999", "Book not found"),
    ("9999", "ISBN9999", "User not found"),
])
def test_borrow_parametrize(lib_init, user_id, isbn, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        lib_init.borrow_book(user_id, isbn)


# =====================================================================
# Cobertura de caja blanca (Tema 8)
# El reporte marcaba como no ejecutado Library.return_book() completo
# y User.register_return(). Esta prueba recorre ese camino.
# =====================================================================
@pytest.mark.unit
def test_library_return_book(lib_init):
    lib = lib_init
    lib.borrow_book("0001", "ISBN0001")
    lib.return_book("0001", "ISBN0001")

    assert lib.books[0].borrowed == False
    assert lib.users[0].get_history() == [
        "Borrowed: Orgullo y prejuicio",
        "Returned: Orgullo y prejuicio",
    ]


@pytest.mark.unit
def test_return_book_not_borrowed(libro):
    with pytest.raises(ValueError, match="The book is not currently borrowed"):
        libro.return_book()


# =====================================================================
# capsys (Tema 11)
# Simulo un uso real del menú y reviso lo que se imprimió.
# =====================================================================
@pytest.mark.unit
def test_capsys(monkeypatch, capsys):
    respuestas = iter(["1", "ISBN001", "U001", "3", "U001", "0"])
    monkeypatch.setattr("builtins.input", lambda mensaje: next(respuestas))

    main.run()

    salida = capsys.readouterr().out
    assert "Book successfully borrowed" in salida
    assert "User history: ['Borrowed: 1984']" in salida