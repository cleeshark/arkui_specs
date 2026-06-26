
@Entry
@Component
export struct Case002ConstraintMinWidth {
  build() {
    Column() {
      Text('Min')
        .id('N_F01_S02_C002_TARGET')
        .width(20)
        .height(50)
        .constraintSize({ minWidth: 80 })
        .backgroundColor('#2196F3')
    }
    .width(300)
    .height(100)
  }
}
