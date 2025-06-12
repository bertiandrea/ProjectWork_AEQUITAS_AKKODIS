Fairness Pipeline Documentation
===============================
Akkodis  è  un’azienda  globale  che  si  occupa  di  consulenza  e  offre  servizi  di  recruiting  e 
formazione. Dal 2022 fa parte del gruppo Adecco, leader a livello mondiale nel reclutamento 
di personale. Questa azienda si distingue nel settore per il suo impegno verso l’inclusività.

**Struttura del Dataset** 
Il  dataset  dell’azienda,  precedentemente  anonimizzato,  presenta  più  righe  per  ciascun 
candidato memorizzato.  
Per  ogni  candidato  ciascuna  riga  identifica  un  diverso  step  nel  processo  di  recruiting.  
Le  colonne  possono  essere  suddivise  in  tre  macrocategorie:  attributi  del  candidato, 
attributi del processo di recruiting  e  attributi della posizione  lavorativa,  associata  al 
candidato.

**ATTRIBUTI del CANDIDATO:** 
- ID: identificatore univoco 
- Candidate State: stato del candidato 
    - Imported: candidati importati da database esterni, come per esempio Alma 
Laurea.  I  candidati  che  mantengono  questo  stato  potrebbero  non  aver  mai 
risposto  ad  Akkodis.  Alcuni  presentano  l’evento  (Event_Type__Val)  CV 
Request, che indica che il recruiter non ha ancora ricevuto il curriculum. 
    - First contact: primi  contatti  con  il  candidato,  normalmente  per  telefono.  I 
candidati che mantengono questo stato potrebbero aver interrotto i contatti 
con  Akkodis  o  potrebbero  non  avere  un  curriculum  adeguato 
(Event_Feedback = Inadequate CV). 
    - In selection: candidati in fase di selezione, sottoposti ai primi colloqui, per 
una posizione lavorativa selezionata tra quelle gestite dalla azienda 
    - QM: candidati sottoposti a Qualification Meeting 
    - Economic Proposal: candidati che hanno ricevuto una proposta economica 
da parte della azienda  
    - Vivier: candidati le cui competenze non sono risultate allineate con i requisiti 
della posizione per cui sono stati valutati, ma sono ritenute valide da Akkodis 
per opportunità future. 
    - Hired il candidato è stato assunto dalla azienda che ha ingaggiato Akkodis 
- Age  Range:  colonna  categorica  contenente  range  di  età 
 [< 20], [20 – 25], [26 – 30], [31 – 35], [36 – 40], [40 – 45], [> 45] 
- Residence: attuale residenza del candidato  
- Sex: sesso del candidato, ammette due valori (Male | Female) e il valore di default è 
Male. 
- Protected  Category:  indica  se  il  candidato  appartiene  alle  categorie  protette, 
specificando l’articolo di riferimento (articoli 1 e 18). 
- TAG: parole chiave utilizzate dal recruiter. 
- Study Area: area di studio, disciplina accademica del candidato. 
- Study Title: laurea o titolo accademico conseguito 
    - Middle school diploma 
    - Professional qualification 
    - High school graduation 
    - Three-year degree 
    - Five-year degree 
    - Master's degree 
    - Doctorate 
- Years  Experience:  range  di  anni  di  esperienza  del  candidato  
[0], [0-1], [1-3], [3-5], [5-7], [7-10], [+10] 
- Sector: settore nel quale il candidato ha esperienza. 
- Last Role: ultimo ruolo lavorativo o di studio del candidato. 
- Year of Insertion: anno di inserimento del candidato nel database. 
- Year of Recruitment: anno di assunzione del candidato, presente solo se Candidate 
State = Hired. 
- Current Ral: RAL attuale del candidato. 
- Expected Ral: aspettativa del candidato sulla RAL futura. 
 
**ATTRIBUTI del PROCESSO:** 
Sono relativi ad uno specifico stadio e cambiano per uno stesso candidato man mano che va 
avanti nel processo di recruiting. 
- Event_Type__Val: specifica il tipo di evento, lo stadio del processo di reclutamento. 
Gli eventi presenti nel database possono essere suddivisi in 3 macrocategorie: 
    - Eventi  iniziali:  Commercial  note,  CV  Request,  Contact  note,  Research 
Association 
    - Eventi  centrali:  HR  interview,  BM  interview,  Technical  interview, 
Qualification Meeting 
    - Eventi finali:  Candidate  notification,  Sending  SC  to  customer,  Economic 
proposal, Notify candidate, Inadequate CV 
- Event_Feedback: feedback associato ad uno specifico evento (Event_Type__Val), 
può essere OK o KO, con eventuali commenti specificati tra parentesi. Non tutti i tipi 
di eventi prevedono un feedback. 
- Overall:  punteggio  associato  al  colloquio,  presente  solo  per  righe  contenenti 
Event_Type__Val centrali, associati a colloqui. 
- Akkodis headquarters: sede di Akkodis che gestisce il candidato. 
Punteggi assegnati dal recruiter, da 1 a 4, durante il colloquio: 
- Technical Skills: competenze tecniche. 
- Standing/Position: posizione all’interno dell’organizzazione. 
- Communication: competenze comunicative. 
- Dynamism: livello di dinamicità. 
- Mobility: mobilità. 
- English: livello di inglese. 

**ATTRIBUTI della POSIZIONE LAVORATIVA:** 
Questi campi sono presenti solo se il candidato è stato assunto dalla azienda in questione. 
- Recruitment Request: richiesta della azienda per un candidato. 
- Assumption Headquarters: sede della posizione lavorativa. 
- Job Family Hiring: categoria della posizione lavorativa. 
- Job Title Hiring: titolo specifico della posizione. 
- Job Description: descrizione del ruolo. 
- Candidate Profile: profilo ideale del candidato, richiesto dalla azienda. 
- Years Experience.1: anni di esperienza richiesti, espressi in range compatibili con 
il campo Years Experience del candidato. 
- Minimum Ral: RAL minima prevista. 
- Ral Maximum: RAL massima prevista. 
- Study Level:  livello  di  studio  richiesto  per  la  posizione  lavorativa,  i  valori  sono 
compatibili con il campo Study Title. 
- Study Area.1: specifica ambito di studio richiesto, contiene compatibili con Study 
Area. 
- Linked_search_key:  campo  contenente  un  codice,  non  univoco,  in  formato 
RSnn.nnnn, nel quale il primo numero a due cifre identifica l’anno di inserimento 
della posizione lavorativa mentre il numero dopo il punto indica il numero di ricerche 
effettuate per una specifica posizione. 

1. Pre-processing
----------------
Carichiamo il dataset, rimuoviamo i duplicati, colonne inutili, righe non desiderate, e applichiamo il remapping definito nel file di configurazione.

**Data Cleaning**
.. code-block:: python

    PATH = 'C:/Users/andre/Desktop/ProjectWork_AEQUITAS_AKKODIS/'
    df = (
        pd.read_excel(PATH + 'data/Dataset_2.0_Akkodis.xlsx')
            .rename(columns=lambda c: c.lstrip().title())
    )
    df = df.drop_duplicates(subset='Id', keep='last')
    df = df.drop(columns=config['drop_columns'])

    for col, remove_list in config['drop_rows'].items():
        df = df[~df[col].isin(remove_list)]

    for col, mapping in config['remap_rows'].items():
        df[col] = df[col].replace(mapping)

.. code-block:: python

    unuseful_columns = []
    for col in df.columns:
        null_count = df[col].isna().sum() / df.shape[0]
        if null_count > (float(config['drop_nan_columns_threshold']) / 100):
            unuseful_columns.append(col)
    df = df.drop(columns=unuseful_columns)

    for col, filler in config['fill_nan_columns'].items():
        if filler == '%MEAN%':
            media = round(df[col].mean())
            df[col].fillna(media, inplace=True)
        else:
            df[col].fillna(filler, inplace=True)

**Feature Mapping**
.. code-block:: python

    def gen_lists(df, specs):
        out = {}
        for name, p in specs.items():
            base = out.get(p['src'], df[p['src']].dropna().astype(str).unique())
            items = [
                x for x in base
                if not any(exc in x for exc in p.get('exc', []))
                   and (any(inc in x for inc in p.get('inc', [])) if 'inc' in p else True)
            ]
            for key in ('split', 'post'):
                if key in p:
                    sep, idx = p[key]
                    items = [x.split(sep)[idx] if sep in x else x for x in items]
            out[name] = sorted(set(items))
        return out

    def apply_field(val, p, lists, feature_cfg):
        if 'list' in p:
            return next((x for x in lists[p['list']] if x in str(val)), p['def'])
        if 'in' in p:
            return p['y'] if val in feature_cfg[p['in']] else p['n']
        if 'eq' in p:
            return p['y'] if str(val) == p['eq'] else p['n']

    for feature, feat_cfg in config['feature_remapping'].items():
        lists = gen_lists(df, feat_cfg['lists'])
        for col_name, col_cfg in feat_cfg['fields'].items():
            df[col_name] = df[col_cfg['src']].apply(lambda v, cfg=col_cfg: apply_field(v, cfg, lists, feat_cfg))
        df = df.drop(columns=feature, errors='ignore')

2. Data Loading & Understanding
-------------------------------
2.1 Feature Selection
~~~~~~~~~~~~~~~~~~~~~
**Target Selection**
L’obiettivo del progetto è lo sviluppo di modelli di AI, da impiegare nelle fasi preliminari 
del processo di recruiting, per analizzare i bias che emergono. La scelta del target è stata 
influenzata  dalla  struttura  del  dataset,  che  contiene  i  candidati  e  le  posizioni  gestiti  da 
Akkodis. 
In  base  ai  dati  disponibili  sono  stati  identificati  due  possibili  obiettivi  per  la  predizione 
automatica:  
- RAL: una nuova colonna per la predizione della RAL più adeguata al profilo del 
candidato.  
- Hired: una nuova colonna che etichetta le coppie candidato-posizione come positive 
o  negative,  definendo  se  il  profilo  del  candidato  sia  adeguato  alle  richieste  della 
azienda. 
La prima ipotesi è stata scartata poiché più del 90% dei candidati non presenta alcun valore 
per nessuno dei campi associati alla RAL.  
D’altra parte, per poter distinguere tra candidati idonei e non idonei, è necessario analizzare 
le tipologie di candidati presenti nel dataset.
La feature target è la variabile che il modello ha il compito di predire.
In questo caso, essa rappresenta l'esito di un processo decisionale, ovvero lo stato di assunzione del candidato.
Tuttavia, il dataset originale non contiene una colonna esplicita binaria per questo scopo.
Pertanto, è stata costruita una variabile target denominata Status, derivata da una combinazione logica di due colonne esistenti: Candidate State ed Event_Feedback.
Questa scelta è coerente con l’obiettivo del progetto, che è valutare se il modello di classificazione rispetti criteri di equità nel processo decisionale relativo all’assunzione dei candidati.

.. code-block:: python

    mask = np.zeros(len(df), dtype=bool)
    for col, valid_values in config['status_positive_conditions'].items():
        mask |= df[col].isin(valid_values)
    df['Status'] = np.where(mask, 'Positive', 'Negative')

**Feature Statistics**
.. code-block:: python

    stats = pd.DataFrame(index=df.columns)
    stats['missing_values'] = df.isnull().sum()
    stats['min'] = df.min(numeric_only=True)
    stats['max'] = df.max(numeric_only=True)
    stats['mean'] = df.mean(numeric_only=True)
    stats['std'] = df.std(numeric_only=True)
    stats['1st_percentile'] = df.quantile(0.25, numeric_only=True)
    stats['2nd_percentile'] = df.quantile(0.50, numeric_only=True)
    stats['3rd_percentile'] = df.quantile(0.75, numeric_only=True)
    stats['type'] = df.dtypes
    stats['distinct_values'] = df.nunique()

    for lookup in config['visualize_columns']:
        distrib = Counter(df[lookup])
        labels = config['categorical_columns_custom_orders'].get(lookup, distrib.keys())
        counts = [distrib[label] for label in labels]
        distrib_df = pd.DataFrame({lookup: labels, 'Count': counts})
        plt.figure(figsize=(8, 5))
        distrib_df.head(20).plot(x=lookup, y='Count', kind='bar', legend=False)
        plt.title(lookup)

**Sensitive Feature Selection**
Nel contesto dell’analisi di equità algoritmica, le variabili considerate sensibili sono state individuate sulla base di criteri normativi (es. GDPR) e di rilevanza sociale, con l’obiettivo di monitorarne l’impatto sui tassi di assunzione e prevenire possibili discriminazioni. In particolare, sono state studiate le seguenti caratteristiche protette:

- **Sesso (Gender)**
Il dataset presenta una marcata sottorappresentazione delle candidate di sesso femminile (20% del totale). Tuttavia, il tasso di assunzione delle donne risulta superiore a quello degli uomini: l’8,3% contro il 5,3%. Questa differenza potrebbe riflettere una scelta organizzativa volta a incrementare la diversità di genere, oppure la maggiore qualificazione dei profili femminili, come suggerito dalla distribuzione dei titoli di studio (titoli di master e dottorato più frequenti tra le donne).
Nonostante ciò, analizzando la RAL massima prevista a parità di titolo di studio e anni di esperienza, le donne ricevono offerte economiche lievemente inferiori. In mancanza di informazioni su orari o tipologia contrattuale non è possibile stabilire se si tratti di disparità ingiustificate o di scelte contrattuali differenziate.

- **Fascia di età (Age Range)**
Più del 65% dei candidati ha meno di 30 anni, di cui il 17% addirittura sotto i 20. Tuttavia, i tassi di assunzione crescono nelle fasce più mature, con un picco tra 31 e 45 anni, a conferma di una preferenza verso professionisti con maggiore esperienza. I candidati più giovani (≤ 26 anni) mostrano performance di assunzione complessivamente inferiori.

- **Residenza europea e italiana**
La residenza in Europa è associata a una probabilità di assunzione superiore rispetto ai residenti extra-UE, probabilmente per motivi di logistica, requisiti legali o presenza di uffici aziendali. All’interno dell’Europa, la residenza in Italia è ulteriormente favorita: il 6% dei residenti italiani viene assunto, contro il 4% dei non residenti. Questa discrepanza permane anche controllando titolo di studio e anni di esperienza, salvo differenze nei range salariali offerti, che risultano più elevati per i non residenti pur a parità di qualifiche.

- **Categoria protetta (Protected Category)**
Gli appartenenti a categorie protette rappresentano soltanto lo 0,6% del campione (18 candidati), un numero troppo esiguo per trarre conclusioni statisticamente significative sul loro tasso di assunzione. In fase di raccolta dati sarà quindi fondamentale aumentare la rappresentatività di questo gruppo per valutare eventuali disparità.

In conclusione, l’analisi delle feature sensibili ha permesso di evidenziare bias potenziali – alcuni forse voluti (ad es. equity di genere), altri non facilmente giustificabili (divario salariale tra uomini e donne, preferenza per residenti italiani).
Il passo successivo consisterà nell’integrare queste valutazioni all’interno del flusso di sviluppo del modello di selezione, applicando metriche di fairness e strumenti di mitigazione per garantire un processo di assunzione equo e trasparente.
.. code-block:: python

    for snstv_col in config['sensitive_columns']:
        order = config['categorical_columns_custom_orders'].get(snstv_col)

        plt.figure(figsize=(8, 5))
        sns.barplot(
            data=df,
            x=snstv_col,
            y=(df['Status'] == 'Positive').astype(float),
            estimator=np.mean,
            order=order,
            hue=snstv_col,
            palette='Set2'
        )
        plt.title(f"Status Positive Rate by {snstv_col}", fontsize=14)
        plt.xticks(rotation=45)

        df_plot = df.copy()
        if order:
            df_plot[snstv_col] = pd.Categorical(df_plot[snstv_col], categories=order, ordered=True)
        
        plt.figure(figsize=(8, 5))
        sns.histplot(
            data=df_plot,
            x=snstv_col,
            hue="Status",
            multiple="stack",
            palette="Set2",
            shrink=0.8
        )
        plt.title(f"Distribution of Status by {snstv_col}", fontsize=14)
        plt.xticks(rotation=45)

2.2 Proxy Identification
~~~~~~~~~~~~~~~~~~~~~~~~
**Cross-Correlation Analysis**
Per evidenziare le relazioni tra le colonne del dataset e ottenere una rappresentazione grafica 
riassuntiva è stata generata una matrice di correlazione, utilizzando la funzione heatmap di 
Seaborn.
.. code-block:: python

    plt.figure(figsize=(16, 10))
    sns.heatmap(df.corr().round(2), annot=True, cmap='coolwarm', center=0, linewidths=.5)
    plt.title("Correlation Matrix of Numerical and Ordered Categorical Features")

.. code-block:: python

    columns_type = {}
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            columns_type[col] = 'cat'
        elif pd.api.types.is_numeric_dtype(df[col]):
            columns_type[col] = 'num'

.. code-block:: python

    num_cols = [col for col, t in columns_type.items() if t == 'num']
    df_num = df[num_cols].copy()

    ordered_categorical_columns = [
        col for col in df.columns if col in config['categorical_columns_custom_orders']
    ]

    df_cat = df[ordered_categorical_columns].copy()

    for col in ordered_categorical_columns:
        order = config['categorical_columns_custom_orders'][col]
        df_cat[col] = pd.Categorical(df_cat[col], categories=order, ordered=True)

    df_cat_encoded = df_cat.apply(lambda x: x.cat.codes)

    df_corr = pd.concat([df_num, df_cat_encoded], axis=1)

    plt.figure(figsize=(16, 10))
    sns.heatmap(df_corr.corr().round(2), annot=True, cmap='coolwarm', center=0, linewidths=.5)
    plt.title("Correlation Matrix of Numerical and Ordered Categorical Features")

.. code-block:: python

    corr_matrix = df_corr.corr().abs()

    # Create a mask to get the upper triangle (excluding the diagonal)
    upper_triangle_mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    upper_triangle = corr_matrix.where(upper_triangle_mask)
    corr_pairs = upper_triangle.stack()

    high_corr_pairs = corr_pairs[corr_pairs > config['correlation_threshold']].sort_values(ascending=False)

    print("Variable pairs with correlation above the threshold:")
    print(high_corr_pairs)

**Chi-squared Test Analysis**
Per identificare le variabili categoriche che potrebbero essere considerate proxy
per le feature sensibili, è stata effettuata un’analisi basata sul test del chi-quadrato.
.. code-block:: python

    def compute(col1, col2):
        order = config['categorical_columns_custom_orders'].get(col1, None)
        contingency = pd.crosstab(df[col1], df[col2])
        if order:
            contingency = contingency.reindex(index=order)
        chi2, p, dof, expected = chi2_contingency(contingency, correction=False)
        test_name = 'Chi-squared'
        if contingency.shape == (2, 2) and (expected < 5).any():
            _, p = fisher_exact(contingency)
            test_name = "Fisher's exact"
        n = contingency.values.sum()
        k = min(contingency.shape)
        cramer_v = np.sqrt(chi2 / (n * (k - 1)))

        return contingency, expected, chi2, p, dof, cramer_v, test_name

    cats = [col for col, t in columns_type.items() if t == 'cat']
    for col1, col2 in combinations(cats, 2):
        if col1 == col2:
            continue
         
        contingency, expected, chi2, p, dof, cramer_v, test_name = compute(col1, col2)

        if p < config['chi_squared_p_value_threshold'] and cramer_v >= config['cramers_v_threshold']:
            print(f"--- {col1} vs {col2} ---")
            #print("Actual frequencies:")
            #print(contingency)
            #print()
            #print("Expected frequencies:")
            #print(pd.DataFrame(expected, index=contingency.index, columns=contingency.columns))
            #print()
            print(f"{test_name} test: χ² = {chi2:.2f}, p = {p:.3f}, dof = {dof}, Cramér’s V = {cramer_v:.3f}")
            print()

2.3 Bias Detection
~~~~~~~~~~~~~~~~~~
Per valutare il livello di Fairness dei modelli addestrati sono state scelte tre metriche: 
- Demographic Parity: Questa metrica richiede che ciascun gruppo abbia le stesse 
opportunità di essere assegnato alla classe positiva (Hired=1), a prescindere che si 
tratti  di  un  vero  o  falso  positivo.  Potrebbe  considerare  come  unfair  un  modello 
accurato, nel caso di sottogruppi sbilanciati nei confronti della colonna target Hired 
nel  test  set.  Per  esempio,  nel  dataset  di  riferimento  le  donne  hanno  un  tasso  di 
assunzione più elevato rispetto agli uomini. Ipotizzando che il test set abbia la stessa 
distribuzione,  un  modello  accurato  potrebbe  essere  considerato  unfair  secondo 
questa  metrica.  Tuttavia,  in  caso  in  cui  il  test  set  presenti  sbilanciamenti  per 
l’etichetta  Hired  causati  da  bias,  questi  vengono  identificati  se  perpetuati  dal 
modello. 
- Equalized Odds:  Questa  metrica  garantisce  che  i  tassi  di  True  Positive  e  False 
Positive  siano  costanti  tra  gruppi  diversi.  Questo  significa,  per  esempio,  che  il 
modello dovrebbe erroneamente classificare come positivi candidati non idonei con 
uguale  probabilità  per  individui  appartenenti  a  categorie  diverse,  senza  favorire 
nessun sottoinsieme.
.. code-block:: python

    def compute_bias_metrics(df, sensitive_column, target_column):
        y_true = (df[target_column] == 'Positive').astype(int)
        y_pred = y_true  # Measuring bias in the true labels
        s_attr = df[sensitive_column]

        dpd = demographic_parity_difference(y_true, y_pred, sensitive_features=s_attr)

        mf = MetricFrame(metrics=selection_rate, y_true=y_true, y_pred=y_pred, sensitive_features=s_attr)
        sr_by_group = mf.by_group
        di = sr_by_group.min() / sr_by_group.max()

        print(f"\n=== Bias metrics for: {sensitive_column} ===")
        print(f"Statistical Parity Difference: {dpd:.4f}")
        print(f"Disparate Impact (min/max rate): {di:.4f}")
        print("\nSelection Rates by group:")
        print(sr_by_group)

    for sensitive_attr in config['sensitive_columns']:
        compute_bias_metrics(df, sensitive_attr, 'Status')

3. Training and Testing
-----------------------
**Dataset Categorical Attributes Sorting and Encoding**
.. code-block:: python

    columns_type = {}
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            columns_type[col] = 'cat'
        elif pd.api.types.is_numeric_dtype(df[col]):
            columns_type[col] = 'num'

    encoding_mappings = {}
    for col in [col for col, t in columns_type.items() if t == 'cat']:
        if col in config['categorical_columns_custom_orders']:
            df[col] = pd.Categorical(df[col], categories=config['categorical_columns_custom_orders'][col], ordered=True).codes
            encoding_mappings[col] = {cat: i for i, cat in enumerate(config['categorical_columns_custom_orders'][col])}
        else:
            encoder = LabelEncoder()
            df[col] = encoder.fit_transform(df[col].astype(str))
            encoding_mappings[col] = dict(zip(encoder.classes_, encoder.transform(encoder.classes_)))

**Models**
Per  garantire  una  panoramica  complessiva  sono  stati  selezionati  modelli  appartenenti  a 
famiglie  algoritmiche  diverse,  includendo  modelli  lineari,  probabilistici,  ad  albero  e  reti 
neurali. L’obiettivo è confrontare i risultati e mettere in relazione performance e fairness. 
I modelli selezionati includono: 
- Modelli Lineari 
    - Linear Regression 
    - Logistic Regression 
- Modelli Probabilistici 
    - Gaussian Naïve Bayes 
- Modelli Tree-based 
    - Decision Tree
- Modelli Distance-based 
    - K-Nearest Neighbors 
- Rete Neurale
 
3.1 Pre-processing Mitigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Pre-processing**
.. code-block:: python

    cr = CorrelationRemover(sensitive_feature_ids=sensitive, alpha=1)

    X_train_cr = cr.fit_transform(train_df)
    X_train_cr_df = pd.DataFrame(X_train_cr)

    X_test_cr = cr.transform(test_df)
    X_test_cr_df = pd.DataFrame(X_test_cr)

**Normalized Coordinate Plot - Original Vs Transformed Dataset**
.. code-block:: python

    X_orig_df = X_train_split.copy()
    X_orig_df.drop(columns=sensitive, inplace=True)
    X_trans_df = X_train_cr_df.copy()

    scaler = MinMaxScaler()
    X_orig_df_scaled = pd.DataFrame(
        scaler.fit_transform(X_orig_df),
        columns=X_orig_df.columns,
        index=X_orig_df.index
    )
    X_trans_df_scaled = pd.DataFrame(
        scaler.fit_transform(X_trans_df),
        columns=X_trans_df.columns,
        index=X_trans_df.index
    )

    X_trans_df_scaled.columns = X_orig_df_scaled.columns
    X_orig_df_scaled['version'] = 'Original'
    X_trans_df_scaled['version'] = 'Transformed'

    df_combined_scaled = pd.concat(
        [X_orig_df_scaled, X_trans_df_scaled],
        ignore_index=True
    )

    plt.figure(figsize=(16, 10))
    parallel_coordinates(
        df_combined_scaled,
        class_column='version',
        cols=list(X_orig_df.columns),
        color=['red', 'blue'],
        alpha=0.3,
        linewidth=0.7
    )

    plt.title("Parallel Coordinates (scaled) – Original vs Transformed")
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Scaled feature value [0–1]")
    plt.grid(axis='y', linestyle='--', linewidth=0.5)

**Coordinate Plot - Original Vs Transformed Dataset**
.. code-block:: python
    
    X_orig_df = X_train_split.copy()
    X_orig_df.drop(columns=sensitive, inplace=True)
    X_trans_df = X_train_cr_df.copy()

    X_trans_df.columns = X_orig_df.columns  # Ensure same columns for comparison
    X_orig_df['version'] = 'Original'
    X_trans_df['version'] = 'Transformed'

    df_combined = pd.concat([X_orig_df, X_trans_df], ignore_index=True)

    plt.figure(figsize=(16, 10))
    parallel_coordinates(
        df_combined,
        class_column='version',
        cols= df_combined.columns[:-1],  # Exclude 'version' column
        color=['red', 'blue'],      # Original→red, Transformed→blue
        alpha=0.3,                  # transparency to see overlap
        linewidth=0.7
    )

    plt.title("Parallel Coordinates – Original vs Transformed")
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Feature value")
    plt.grid(axis='y', linestyle='--', linewidth=0.5)  # light horizontal grid

**Models**
.. code-block:: python

    def create_model(seed, input_dim):
        tf.random.set_seed(seed)
        model = Sequential()
        model.add(Dense(128, input_dim=input_dim, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(128, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(128, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(64, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(1, activation='sigmoid'))

        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    models = {
        'Logistic Regression': LogisticRegression(),
        'Linear Regression': LinearRegression(),
        'Decision Tree': DecisionTreeClassifier(),
        'Naive Bayes': GaussianNB(),
        'XGBoost': XGBClassifier(),
        'KNN': KNeighborsClassifier(),
        'Neural Network': create_model(random_seed, X_train_cr_df.shape[1]),
    }

**Training**
.. code-block:: python

    for model_name, model in models.items():
        print(f"Training {model_name}...")
        if model_name == 'Neural Network':
            model.fit(X_train_cr_df, y_train_split, epochs=10, batch_size=32, verbose=0)
            predictions[f"{model_name}_preprocessed_cr"] = model.predict(X_test_cr_df).flatten()
        else:
            model.fit(X_train_cr_df, y_train_split)
            predictions[f"{model_name}_preprocessed_cr"] = model.predict(X_test_cr_df)

        if model_name in ['Linear Regression', 'XGBoost', 'Neural Network']:
            predictions[f"{model_name}_preprocessed_cr"] = (predictions[f"{model_name}_preprocessed_cr"] > 0.5).astype(int)
        
        print(f"{model_name} trained.")
        temp = predictions[f"{model_name}_preprocessed_cr"]
        print(f"Preprocessed predictions for {model_name}: {temp}")
    
3.2 In-processing Mitigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Models**
.. code-block:: python

    models = {
        'Linear Regression': LinearRegression(),
    }

**In-processing and Training**
.. code-block:: python

    for model_name, model in models.items():
        gfc = GerryFairClassifier(
            C=10,
            gamma=0.01,
            fairness_def='FP',
            max_iters=10,
            printflag=False,
            heatmapflag=False,
            heatmap_iter=10,
            heatmap_path='.',
            predictor=model
        )
        gfc.fit(train_ds)
        pred_gfc = gfc.predict(test_ds)
        predictions[f"{model_name}_inprocessed_gfc"] = pred_gfc.labels.ravel()
        temp = predictions[f"{model_name}_inprocessed_gfc"]
        print(f"Inprocessed predictions for {model_name}: {temp}")

3.3 Post-processing Mitigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Models**
.. code-block:: python

    def create_model(seed, input_dim):
        tf.random.set_seed(seed)
        model = Sequential()
        model.add(Dense(128, input_dim=input_dim, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(128, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(128, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(64, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dense(1, activation='sigmoid'))

        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    models = {
        'Logistic Regression': LogisticRegression(),
        'Linear Regression': LinearRegression(),
        'Decision Tree': DecisionTreeClassifier(),
        'Naive Bayes': GaussianNB(),
        'XGBoost': XGBClassifier(),
        'KNN': KNeighborsClassifier(),
        'Neural Network': create_model(random_seed, train_df.shape[1]),
    }

**Training**
.. code-block:: python

    for model_name, model in models.items():
        print(f"Training {model_name}...")
        if model_name == 'Neural Network':
            model.fit(train_df, y_train_split, epochs=10, batch_size=32, verbose=0)
            predictions[f"{model_name}_postprocessed_to"] = model.predict(test_df).flatten()
        else:
            model.fit(train_df, y_train_split)
            predictions[f"{model_name}_postprocessed_to"] = model.predict(test_df)

        print(f"{model_name} trained.")

**Post-processing**
.. code-block:: python

    for model_name, model in models.items():
        to = ThresholdOptimizer(
            estimator=model,
            constraints='demographic_parity',
            objective='accuracy_score',
            prefit=True,
            grid_size=1000,
            flip=False,
            predict_method='predict'
        )
        to.fit(train_df, y_train_split, sensitive_features=s_train_split)
        pred_to = to.predict(test_df, sensitive_features=s_test_split)
        predictions[f"{model_name}_postprocessed_to"] = pred_to.ravel()
        temp = predictions[f"{model_name}_postprocessed_to"]
        print(f"Postprocessed predictions for {model_name}: {temp}")

3. Performance and Fairness Metrics Evaluation
-----------------------
**Performance Metrics**
 - Accuracy
 - Precision
 - Recall
 - F1-score
 - AUC

.. code-block:: python

    records = []
    for name, y_pred in predictions_df.items():
        scores = {
            'Model':      name,
            'Accuracy':   accuracy_score(y_test, y_pred),
            'Precision':  precision_score(y_test, y_pred),
            'Recall':     recall_score(y_test, y_pred),
            'F1-score':   f1_score(y_test, y_pred),
            'ROC AUC':    roc_auc_score(y_test, y_pred),
            'Group':      'Processed' if any(tag in name for tag in ['preprocessed','inprocessed','postprocessed'])
                        else 'Base'
        }
        records.append(scores)

    df = pd.DataFrame(records).round(3)

    df_long = df.melt(id_vars=['Model','Group'],
                    value_vars=['Accuracy','Precision','Recall','F1-score','ROC AUC'],
                    var_name='Metric',
                    value_name='Value')

    base_models = df.loc[df.Group=='Base','Model'].unique()

    ncols = 3
    nrows = int(np.ceil(len(base_models)/ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols*4, nrows*3), sharey=True)
    axes = axes.flatten()

    for ax, base in zip(axes, base_models):
        sel = df_long[df_long['Model'].str.startswith(base)]
        
        pivot = sel.pivot(index='Metric', columns='Model', values='Value')
        variants = pivot.columns.tolist()
        x = np.arange(len(pivot))
        width = 0.8 / len(variants)

        for i, var in enumerate(variants):
            label = var.replace(base + '_', '') if var != base else 'Base'
            ax.bar(x + (i - (len(variants)-1)/2)*width, pivot[var], width, label=label)

        ax.set_xticks(x)
        ax.set_xticklabels(pivot.index, rotation=45, ha='right')
        ax.set_title(base)
        ax.legend(fontsize='x-small')

    for ax in axes[len(base_models):]:
        ax.set_visible(False)

    plt.tight_layout()
    plt.show()

**Fairness Metrics**
 - Demographic Parity Ratio
 - Equalized Odds Ratio
 - Demographic Parity Difference
 - Equalized Odds Difference

.. code-block:: python

    def compute_fairness_metrics(y_true, y_pred, s_test, label=None):
        mf = MetricFrame(
            metrics={
                'selection_rate': selection_rate,
                'fpr': false_positive_rate,
                'fnr': false_negative_rate,
                'count': count
            },
            y_true=y_true,
            y_pred=y_pred,
            sensitive_features=s_test
        )

        dp_diff = demographic_parity_difference(y_true, y_pred, sensitive_features=s_test)
        eo_diff = equalized_odds_difference(y_true, y_pred, sensitive_features=s_test)

        dp = demographic_parity_ratio(y_true, y_pred, sensitive_features=s_test)
        eo = equalized_odds_ratio(y_true, y_pred, sensitive_features=s_test)

        if label:
            print(f"=== {label} ===")

        print("By group:")
        print(mf.by_group)
        print()
        print("Overall (selection_rate, fpr, fnr, count):")
        print(mf.overall)
        print()
        print(f"Demographic parity difference: {dp_diff:.4f}")
        print(f"Equalized odds difference:     {eo_diff:.4f}\n")
        print()
        print(f"Demographic parity ratio: {dp:.4f}")
        print(f"Equalized odds ratio:     {eo:.4f}\n")

        return mf

    for name in predictions_df.columns:
        compute_fairness_metrics(y_test, predictions_df[name], s_test, label=name)
