#libraries
from playwright.sync_api import sync_playwright
from playwright.sync_api import Page #type

#own files
from utils.save_csv import save_csv


def scrap(page: Page,subject_code:str,list_of_subjects : list,visited_courses:set):

    #the identifiers on the web
    id_subject_name = "#ctl00_contenido_LabelNombreMateria"
    id_subject_parallel = "#ctl00_contenido_LabelParalelo" #this is 'paralelo'
    id_teacher_name = "#ctl00_contenido_LabelProfesor"
    id_amount_permitted_students = "#ctl00_contenido_LabelCupo"
    id_amount_available_spaces = "#ctl00_contenido_LabelDisponible"
    id_date_first_exam = "#ctl00_contenido_LabelParcial"
    id_date_second_exam = "#ctl00_contenido_LabelFinal"
    id_date_third_exam = "#ctl00_contenido_LabelMejora"
    id_aula_first_exam = "#ctl00_contenido_aulaParcial"
    id_aula_second_exam = "#ctl00_contenido_aulaFinal"
    id_aula_third_exam = "#ctl00_contenido_aulaMej"
    id_table_with_theorical_contents = "#ctl00_contenido_TableHorarios"

    #the important data to pull
    name_of_subject = page.locator(id_subject_name).inner_text().strip()
    parallel = page.locator(id_subject_parallel).inner_text().strip()
    teacher_name = page.locator(id_teacher_name).inner_text().strip()
    permitted_students = page.locator(id_amount_permitted_students).inner_text().strip()
    available_spaces = page.locator(id_amount_available_spaces).inner_text().strip()
    date_first_exam = page.locator(id_date_first_exam).inner_text().strip()
    date_second_exam = page.locator(id_date_second_exam).inner_text().strip()
    date_third_exam = page.locator(id_date_third_exam).inner_text().strip()
    aula_first_exam = page.locator(id_aula_first_exam).inner_text().strip()
    aula_second_exam = page.locator(id_aula_second_exam).inner_text().strip()
    aula_third_exam = page.locator(id_aula_third_exam).inner_text().strip()

    #extract the list of associated practical parallels linked to this theory parallel
    paralelos_asociados = [
        a.inner_text().strip()
        for a in page.locator("a.mostrar").all()
    ]

    #this makes sure that you don't pull the same data twice (the data for a subject and parallel that you already had)
    unique_id = f"{subject_code}-{parallel}"
    if unique_id in visited_courses:
        return
    
    #if unique_id not in visited_courses, then you add it because now you're on it
    visited_courses.add(unique_id)

    #extract data from the teoric course
    table_dates_rows = page.locator(f"{id_table_with_theorical_contents} tbody tr")
    
    for row in range(table_dates_rows.count()):
        cells_of_the_row = table_dates_rows.nth(row).locator("td").all_inner_texts()

        if(len(cells_of_the_row) >= 4):
            list_of_subjects.append({
                "Codigo Materia": subject_code.upper(),
                "Materia": name_of_subject,
                "Tipo": "Teoria",
                "Paralelo": parallel,
                "Profesor": teacher_name,
                "Cupo Maximo": permitted_students,
                "Cupo Disponible": available_spaces,
                "Planificada Quincenalmente": "no",
                "Examen Parcial": date_first_exam,
                "Aula Examen Parcial": aula_first_exam,
                "Examen Final": date_second_exam,
                "Aula Examen Final": aula_second_exam,
                "Mejoramiento": date_third_exam,
                "Aula Mejoramiento": aula_third_exam,
                "Paralelos Asociados": ", ".join(paralelos_asociados),
                "Dia": cells_of_the_row[0].strip(),
                "Hora Inicio": cells_of_the_row[1].strip(),
                "Hora Fin": cells_of_the_row[2].strip(),
                "Aula": cells_of_the_row[3].strip(),
                "Bloque": cells_of_the_row[4].strip() if len(cells_of_the_row) > 4 else ""
            })

    
    #extract data from practice
    """
    we do this because teoric may have only a restricted practice
    or a you can choose any of the availables practices
    Example:
    MATG1032  theory:P3 -> practice:103
    MATG1032  theory:P4 -> practice:104

    TLMG1032  theory:P1 -> practice:105 107 102 109 103 106 112 115 108 110 113 114
    in the first one you're restrictes and in the second one you're not
    """
    id_practice_divs = "div.tabla_horario"
    practice_divs = page.locator(id_practice_divs)

    #TODO: YOU NEED TO KEEP IN MIND THE SUBJECTS PLAINFIED ON THE 15TH
    for i in range(practice_divs.count()):
        practice_div = practice_divs.nth(i)

        first_table = practice_div.locator("table").first
        text_info = first_table.locator("td").all_inner_texts()
        practice_teacher_name = ""
        practice_parallel = ""
        practice_planificada_quincenalmente = "no"
        practice_capacidad = ""
        practice_cupo_disponible = ""
        
        #this is to remove extra text we do not need
        for text in text_info:
            cleaned = text.strip()
            if "Profesor:" in cleaned:
                practice_teacher_name = cleaned.replace("Profesor:", "").strip()
            elif "Paralelo::" in cleaned or "Paralelo:" in cleaned:
                practice_parallel = cleaned.replace("Paralelo::", "").replace("Paralelo:", "").strip()
            elif "Planificada quincenalmente:" in cleaned:
                # the value is in the next td; captured in the loop already as separate entry
                pass
            elif "Capacidad:" in cleaned:
                practice_capacidad = cleaned.replace("Capacidad:", "").strip()
            elif "Cupo disponible:" in cleaned:
                practice_cupo_disponible = cleaned.replace("Cupo disponible:", "").strip()

        # Planificada quincenalmente value is the td right after the label td
        all_tds = first_table.locator("td").all_inner_texts()
        for idx, td_text in enumerate(all_tds):
            if "Planificada quincenalmente:" in td_text and idx + 1 < len(all_tds):
                practice_planificada_quincenalmente = all_tds[idx + 1].strip()
                break

        ##extract data from the practice course
        # NOTE: the selector is "table.display" (element.class), not ".table.display" (two classes)
        rows_table = practice_div.locator("table.display tbody tr")
        for j in range(rows_table.count()):
            cells_of_the_row = rows_table.nth(j).locator("td").all_inner_texts()
            if len(cells_of_the_row) >= 4:
                list_of_subjects.append({
                    "Codigo Materia": subject_code.upper(),
                    "Materia": name_of_subject,
                    "Tipo": "Practico",
                    "Paralelo": practice_parallel,
                    "Profesor": practice_teacher_name,
                    "Cupo Maximo": practice_capacidad,
                    "Cupo Disponible": practice_cupo_disponible,
                    "Planificada Quincenalmente": practice_planificada_quincenalmente,
                    "Examen Parcial": date_first_exam,
                    "Aula Examen Parcial": aula_first_exam,
                    "Examen Final": date_second_exam,
                    "Aula Examen Final": aula_second_exam,
                    "Mejoramiento": date_third_exam,
                    "Aula Mejoramiento": aula_third_exam,
                    "Paralelos Asociados": ", ".join(paralelos_asociados),
                    "Dia": cells_of_the_row[0].strip(),
                    "Hora Inicio": cells_of_the_row[1].strip(),
                    "Hora Fin": cells_of_the_row[2].strip(),
                    "Aula": cells_of_the_row[3].strip(),
                    "Bloque": cells_of_the_row[4].strip() if len(cells_of_the_row) > 4 else ""
                })


def get_parallels_specific_subject(page: Page, url: str) -> list:
    id_search_button = "#ctl00_contenido_Button2"
    id_links_to_classes = ".myLink"
    id_error_message = "#ctl00_contenido_LabelError"

    # click to show the teoric parallels of that subject
    page.locator(id_search_button).click()

    if "captcha" in page.url.lower():
        input("soluciona el captcha y luego dale enter para continuar con el scappeo")
    # if there is an error returns an empty list
    #if not just continues
    try:
        page.wait_for_selector(id_error_message, timeout=1500, state="visible")
        print("Mensaje de error detectado: No existen datos para mostrar.")
        return []
    except Exception:
        pass

    #waits for the links to be visible on the dom, if they do not show
    #just returns an empty list
    try:
        page.locator(id_links_to_classes).first.wait_for(state="visible", timeout=5000)
    except Exception:
        page.goto(url)
        return []
    
    #extract all links
    links_to_parallels = page.locator(id_links_to_classes).all()
    
    return links_to_parallels
    
def fill_info_specific_subject(code:str, year:int, term:int, page:Page, url:str) -> bool:
    print(f"subject : {code}, the year is {year}, term is {term}")

    # the identifiers on the web
    id_year_input = "#ctl00_contenido_txtAnio"
    id_term_clickable = "#ctl00_contenido_listab_1" if term == 1 else "#ctl00_contenido_listab_2" if term == 2 else "#ctl00_contenido_listab_0"
    id_consult_button = "#ctl00_contenido_btnConsultar"
    id_code_clickable = "#ctl00_contenido_RBList_1"
    id_code = "#ctl00_contenido_codigoMateria"

    page.locator(id_year_input).clear()
    page.locator(id_year_input).fill(str(year))
    page.locator(id_term_clickable).click()
    page.locator(id_consult_button).click()
    page.locator(id_code_clickable).wait_for(state="attached")
    page.locator(id_code_clickable).click()

    # Bucle de comprobación activa (máximo 15 segundos)
    is_enabled = False
    for _ in range(15):
        if "captcha" in page.url.lower():
            print("🚨 CAPTCHA detectado al intentar habilitar el campo de código.")
            input("Resuelve el captcha en el navegador y presiona ENTER aquí en la terminal...")
            page.goto(url)
            return False # Indica que la operación falló por interrupción
        
        # Evaluar si el elemento existe y ya no está deshabilitado
        if page.evaluate(f'() => document.querySelector("{id_code}") && document.querySelector("{id_code}").disabled === false'):
            is_enabled = True
            break
            
        page.wait_for_timeout(1000)

    if not is_enabled:
        print("El campo nunca se habilitó (posible caída de conexión de ESPOL). Saltando...")
        page.goto(url)
        return False

    page.locator(id_code).clear()
    page.locator(id_code).fill(code)
    return True


def search_by_code_and_year(
        code: str,
        year:int,
        term:int,
        url:str,
        page:Page,
        list_of_subjects: list,
        visited_courses : set
    )->None:

    # Recibir el estado de éxito y pasar el url
    success = fill_info_specific_subject(code=code, year=year, term=term, page=page, url=url)
    
    # Si la función retornó False (por CAPTCHA o lag), se aborta esta materia
    if not success:
        return 

    links_to_parallels = get_parallels_specific_subject(page=page,url=url)

    if len(links_to_parallels) <= 0:
        page.goto(url)
        return
     
    urls_to_visit = []
    for link_to_parallel in links_to_parallels:
        href = link_to_parallel.get_attribute("href")
        if href:
            full_url = f"https://www.academico.espol.edu.ec/UI/Registros/{href}"
            urls_to_visit.append(full_url)
    
    for full_url in urls_to_visit:
        page.goto(full_url)
        scrap(page=page, subject_code=code, list_of_subjects=list_of_subjects, visited_courses=visited_courses)
    
    page.goto(url)
    

with sync_playwright() as p:
    URL = "https://www.academico.espol.edu.ec/UI/Registros/horariosplanificados.aspx"
    YEAR = 2026
    TERM = 2 #this refers to the PAO also handles vacational period (any value different than 1 or 2 are handled as vacational period)
    CODE = "ELEG".lower() #this could be MATG also or sum like that
    START = 1028
    STOP = 1052
    codes = [CODE + str(number) for number in range(START,STOP + 1)]
    #codes = ["eleg1028"]

    list_of_subjects = []
    visited_courses = set() #a set only has unique elements 
    browser = p.firefox.launch(headless=False, args=["--start-maximized"])
    page = browser.new_page()
    page.goto(URL)

    print("""
          Inicia sesión y dirigete a 
          https://www.academico.espol.edu.ec/UI/Registros/horariosplanificados.aspx
          """)
    
    page.wait_for_url("**/horariosplanificados.aspx", timeout=300000)

    #once logged in you can start scrapping
    for code in codes:
        
        search_by_code_and_year(
            code=code,
            year=YEAR,
            term=TERM,
            url=URL,
            page=page,
            list_of_subjects=list_of_subjects,
            visited_courses=visited_courses
        )
        """
        wait_time = random.uniform(2.0,5.0)
        print("esperando a propósito para evitar el captcha de espol")
        time.sleep(wait_time)
        """
    browser.close()
    
    # Export collected data to CSV
    save_csv(list_of_subjects)