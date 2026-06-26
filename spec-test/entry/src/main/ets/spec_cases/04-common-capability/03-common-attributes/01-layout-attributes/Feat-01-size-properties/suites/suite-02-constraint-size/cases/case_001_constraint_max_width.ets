
@Entry
@Component
export struct Case001ConstraintMaxWidth {
  build() {
    Column() {
      Text('Constrained')
        .id('N_F01_S02_C001_TARGET')
        .width(200)
        .height(50)
        .constraintSize({ maxWidth: 100 })
        .backgroundColor('#4CAF50')
    }
    .width(300)
    .height(100)
  }
}
