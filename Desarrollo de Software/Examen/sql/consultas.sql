-- Fase 4 — Consultas Analíticas

-- 1. Ingreso total y ticket promedio por especialidad
-- Interpretación: Los servicios de citas médicas se caracterizan por tener precios variados, siendo
-- especialemente altos aquellos que impliquen una mayor complejidad o más bajos aquellos que sean
-- servicios más básicos. El fin de esta consulta es precisamente diferenciar las especialidades
-- según este criterio, básicamente, permite identificar qué especialidades generan más ingresos y
-- cuáles tienen mayor ticket promedio. 

-- Para ejecutar: sqlite3 data/clinica_curated.db < sql/consultas.sql

SELECT 
    specialty_clean AS especialidad,
    COUNT(*) AS total_citas,
    ROUND(SUM(amount_charged_clean), 2) AS ingreso_total,
    ROUND(AVG(amount_charged_clean), 2) AS ticket_promedio,
    ROUND(AVG(amount_charged_clean) / 100, 2) AS ticket_promedio_en_centenas
FROM fact_appointments
WHERE status != 'cancelada'  -- Citas que generaron ingreso
GROUP BY specialty_clean
ORDER BY ingreso_total DESC;


-- 2. Tasa de no-show por sucursal
-- Interpretación: Identifica qué sucursales tienen una tasa de no-show superior al promedio
-- general. Básicamente, funciona como indicador de problemas en la sucursal, ya que la presecia
-- de una tasa alta indica que hay un mal funcionamiento en la sucursal que provoca que los clientes
-- no se presenten a sus citas. En otras palabras, es posible detectar el problema de raíz si se
-- detecta que existe uno. Por ejemplo, pueden tener problemas de accesibilidad o mala comunicación, 
-- factores que no se ven directamente en los datos, pero que si impactan en ellos, por lo que al 
-- detectarlos es posible darles a estas sucursales la atención que requieren para tratar el problema
-- en cuestión-

WITH no_show_metrics AS (
    SELECT 
        clinic_code_clean AS sucursal,
        COUNT(*) AS total_citas,
        SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS no_show_count,
        ROUND(CAST(SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS tasa_no_show
    FROM fact_appointments
    GROUP BY clinic_code_clean
),
promedio_general AS (
    SELECT 
        ROUND(CAST(SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS promedio_general
    FROM fact_appointments
)
SELECT 
    m.sucursal,
    m.total_citas,
    m.no_show_count,
    m.tasa_no_show || '%' AS tasa_no_show,
    p.promedio_general || '%' AS promedio_general,
    ROUND(m.tasa_no_show - p.promedio_general, 2) AS diferencia_porcentual
FROM no_show_metrics m
CROSS JOIN promedio_general p
WHERE m.tasa_no_show > p.promedio_general
ORDER BY m.tasa_no_show DESC;


-- 3. Ingreso mensual por sucursal y variación contra el mes anterior
-- Interpretación: Las variaciones, tanto positivas como negativas, pueden servir para identificar
-- tendencias estacionales o ser el reflejo de implementaciones por parte de las sucursales que pueden
-- estar impactando en su desempeño. Por ejemplo, un aumento de la demanda de servicios en diciembre 
-- (mayor ingreso) en diciembre puede indicar un aumento en la demanda por la temporada invernal y 
-- las enfermedades que acarrea, lo que puede aprovecharse para maximizar aún más las ventas; mietras que
-- una variación negativa puede ser explicada por la apertura de una sucursal de la competencia en la
-- zona, lo que hace menos atractiva la oferta en la sucursal evaluada y podría evaluarse la situación
-- para mejorar los ingresos.

WITH ingresos_mensuales AS (
    SELECT 
        clinic_code_clean AS sucursal,
        strftime('%Y-%m', scheduled_at) AS mes,
        ROUND(SUM(amount_charged_clean), 2) AS ingreso_mensual,
        COUNT(*) AS total_citas
    FROM fact_appointments
    WHERE status != 'cancelada'
    GROUP BY clinic_code_clean, strftime('%Y-%m', scheduled_at)
),
variacion AS (
    SELECT 
        sucursal,
        mes,
        ingreso_mensual,
        total_citas,
        LAG(ingreso_mensual) OVER (PARTITION BY sucursal ORDER BY mes) AS ingreso_mes_anterior,
        LAG(total_citas) OVER (PARTITION BY sucursal ORDER BY mes) AS citas_mes_anterior,
        ROUND(
            (ingreso_mensual - LAG(ingreso_mensual) OVER (PARTITION BY sucursal ORDER BY mes)) 
            / NULLIF(LAG(ingreso_mensual) OVER (PARTITION BY sucursal ORDER BY mes), 0) * 100, 
            2
        ) AS variacion_porcentual
    FROM ingresos_mensuales
)
SELECT 
    sucursal,
    mes,
    '$' || ingreso_mensual AS ingreso_mensual,
    total_citas AS citas_del_mes,
    '$' || ingreso_mes_anterior AS ingreso_mes_anterior,
    citas_mes_anterior AS citas_mes_anterior,
    CASE 
        WHEN variacion_porcentual IS NULL THEN 'N/A (primer mes)'
        WHEN variacion_porcentual > 0 THEN '+' || variacion_porcentual || '%'
        ELSE variacion_porcentual || '%'
    END AS variacion,
    CASE 
        WHEN variacion_porcentual > 0 THEN 'Aumento'
        WHEN variacion_porcentual < 0 THEN 'Disminución'
        ELSE 'Sin cambio'
    END AS tendencia
FROM variacion
WHERE mes >= '2024-01'
ORDER BY sucursal, mes;


-- 4. Top 10 de pacientes por número de citas y revenue_gap acumulado
-- Interpretación: Permite identificar tipos de pacientes importantes para el negocio. Por un lado,
-- los pacientes más frecuentes son aqullos que aportan más valor al negocio, pues su inversión en 
-- el es constante, por lo que conviene identificarlos y recompensarlos para que continuen manteniendo
-- ese status. Por otro lado, evaluar el revenue_gap también es importante porque permite identificar
-- a pacientes frecuentes con descuentos excesivos o problemas con el asegurador (no son redituables, 
-- por lo que conviene identificarlos).

WITH paciente_metricas AS (
    SELECT 
        patient_id,
        COUNT(*) AS total_citas,
        ROUND(SUM(amount_charged_clean), 2) AS total_gastado,
        ROUND(AVG(amount_charged_clean), 2) AS ticket_promedio,
        ROUND(SUM(revenue_gap), 2) AS revenue_gap_acumulado,
        ROUND(AVG(revenue_gap), 2) AS revenue_gap_promedio,
        ROUND(AVG(patient_age_at_visit), 0) AS edad_promedio
    FROM fact_appointments
    GROUP BY patient_id
)
SELECT 
    patient_id AS id_paciente,
    total_citas AS numero_citas,
    '$' || total_gastado AS total_gastado,
    '$' || ticket_promedio AS ticket_promedio,
    '$' || revenue_gap_acumulado AS revenue_gap_acumulado,
    '$' || revenue_gap_promedio AS gap_promedio_por_cita,
    edad_promedio || ' años' AS edad_promedio,
    CASE 
        WHEN revenue_gap_acumulado < -1000 THEN 'Descuento alto'
        WHEN revenue_gap_acumulado < -100 THEN 'Descuento moderado'
        ELSE 'Sin descuento significativo'
    END AS clasificacion
FROM paciente_metricas
ORDER BY total_citas DESC
LIMIT 10;


-- 5. Distribución de motivos de rechazo por mes
-- Interpretación: Permite identificar patrones en los rechazos para poder atenderlos
-- de manera correcta. Por ejemplo, es posible reconocer patrones que indiquen problemas
-- con los formularios de registro o problemas durante el proceso).

WITH rechazos_por_mes AS (
    SELECT 
        strftime('%Y-%m', ingested_at) AS mes,
        reject_reason
    FROM quarantine
    WHERE source = 'appointments'
),
rechazos_desglosados AS (
    SELECT 
        mes,
        TRIM(value) AS motivo
    FROM rechazos_por_mes,
    json_each('["' || REPLACE(reject_reason, ';', '","') || '"]')
    WHERE reject_reason != ''
),
conteo_motivos AS (
    SELECT 
        mes,
        motivo,
        COUNT(*) AS cantidad
    FROM rechazos_desglosados
    WHERE motivo != ''
    GROUP BY mes, motivo
),
totales_mes AS (
    SELECT 
        mes,
        SUM(cantidad) AS total_mes
    FROM conteo_motivos
    GROUP BY mes
)
SELECT 
    c.mes AS mes,
    c.motivo AS motivo_rechazo,
    c.cantidad AS cantidad,
    t.total_mes AS total_rechazos_mes,
    ROUND(CAST(c.cantidad AS FLOAT) / t.total_mes * 100, 2) || '%' AS porcentaje_del_mes,
    CASE 
        WHEN CAST(c.cantidad AS FLOAT) / t.total_mes >= 0.30 THEN '██████████'
        WHEN CAST(c.cantidad AS FLOAT) / t.total_mes >= 0.20 THEN '████████'
        WHEN CAST(c.cantidad AS FLOAT) / t.total_mes >= 0.10 THEN '██████'
        WHEN CAST(c.cantidad AS FLOAT) / t.total_mes >= 0.05 THEN '████'
        ELSE '██'
    END AS barra_visual
FROM conteo_motivos c
JOIN totales_mes t ON c.mes = t.mes
ORDER BY c.mes DESC, c.cantidad DESC;