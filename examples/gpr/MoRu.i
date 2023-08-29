[Mesh]
  type = GeneratedMesh
  dim = 1
  nx = 100
  xmax = 1
[]
[GlobalParams]
  elements = 'Mo Ru'
  output_phases = 'BCCN HCPN'
  output_species = 'BCCN:Mo HCPN:Mo BCCN:Ru HCPN:Ru'
  output_element_potentials = 'mu:Mo mu:Ru'
  output_vapor_pressures = 'vp:gas_ideal:Mo'
  output_element_phases = 'ep:BCCN:Mo'
[]

[ChemicalComposition]
  thermofile = Kaye_NobleMetals.dat
  tunit = K
  punit = atm
  munit = moles
  temperature = T
  output_species_unit = mole_fraction
[]

[Variables]
  [T]
  []
[]

[ICs]
  [Mo]
    type = FunctionIC
    variable = Mo
    function = '0.8*(1-x)+4.3*x'
  []
  [Ru]
    type = FunctionIC
    variable = Ru
    function = '0.2*(1-x)+4.5*x'
  []
[]

[Problem]
  solve = false
[]

[Executioner]
  type = Steady
[]

[Postprocessors]
  [avg]
    type = AverageNodalVariableValue
    variable = mu:Mo
  []
  [max]
    type = NodalExtremeValue
    variable = mu:Ru
    value_type = max
  []
[]

[Outputs]
[]
